import psycopg2
import requests
from decimal import *

API_BASE = "https://api.coinmarketcap.com/v1/ticker/"


def query_portfolio(db):
    conn = psycopg2.connect("dbname=" + db)
    cursor = conn.cursor()

    return cursor


def print_header():
    print()
    print('Symbol'.ljust(8),
          '| Coin Value'.ljust(19),
          '| Total Worth'.ljust(20),
          '| Fiat Gain/Loss'.ljust(20),
          '| % Gain/Loss'.ljust(17),
          '| # Coins Owned'.ljust(19),
          '| Amount Invested'.ljust(21),
          '| Avg Cost Per Coin'.ljust(21))


def print_portfolio_data(sorted_assets):
    for data in sorted_assets:
        # This separation allowed the figures to right justify while still appending a dollar sign to the front.
        num_coins = str("{:,.4f}").format(data["num_coins"])
        avg_cost = '$ ' + str("{:,.2f}").format(data["avg_cost"])
        coin_value = '$ ' + str("{:,.2f}").format(data["coin_value"])
        diff_in_price = '$ ' + str("{:,.2f}").format(data["delta_price"])
        total_cost = '$ ' + str("{:,.2f}").format(data["total_cost"])
        total_value = '$ ' + str("{:,.2f}").format(data["total_value"])

        print('-' * 165)
        print(" {:<8} {:>16} {:>20} {:>20} {:>17.2%} {:>19} {:>21} {:>23}".format(
            data["symbol"],
            coin_value,
            total_value,
            diff_in_price,
            data["percent_of_cost"],
            num_coins,
            total_cost,
            avg_cost))


def print_total_gains(holdings):
    total_gains = 0
    total_invested = 0

    for coin in holdings:
        total_invested += coin["total_cost"]
        total_gains += coin["total_value"]

    total_worth = total_gains - total_invested

    stars = '*' * 110
    print("\n\n" + stars + "\n")
    print(" \t\t Total Gain/Loss: ${:,.2f} \t***  Total Value: ${:,.2f} \t***  Total Invested: ${:,.2f}"
          .format(total_gains, total_worth, total_invested))
    print("\n" + stars)


def merge_and_average_txn_data(cursor):
    sums = {}
    coins = {}

    cursor.execute("""
    SELECT co.coin_id, co.coin_symbol, co.coin_name, t.num_shares, t.share_price 
    FROM transactions as t
    JOIN coins as co ON co.coin_id = t.coin_id  
    ORDER BY t.coin_id;
    """)
    txns = cursor.fetchall()

    for i in range(0, len(txns)):
        coin_id = txns[i][0]
        if coin_id not in sums:
            sums[coin_id] = txns[i][3]
            coins[coin_id] = {}
            coins[coin_id]['coin_id'] = txns[i][0]
            coins[coin_id]['symbol'] = txns[i][1]
            coins[coin_id]['coin_name'] = txns[i][2]
            coins[coin_id]['avg_cost'] = 0
            coins[coin_id]['num_coins'] = txns[i][3]
        else:
            sums[coin_id] += txns[i][3]
            coins[coin_id]['num_coins'] += txns[i][3]

    for i in range(0, len(txns)):
        coin_id = txns[i][0]
        coins[coin_id]['avg_cost'] += (Decimal(txns[i][3]) / Decimal(sums[coin_id])) * Decimal(txns[i][4])

    for id in coins.keys():
        coins[id]['total_cost'] = coins[id]['avg_cost'] * coins[id]['num_coins']

    return coins


def query_market_data(coins):
    for id in coins.keys():

        url = API_BASE + coins[id]['coin_name']
        coin_req = requests.get(url)
        # also contains % change over 1h, 24h, 7d, market cap, volume over 24 hours, rank
        coin_res = coin_req.json()

        coins[id]["coin_value"] = Decimal(coin_res[0]['price_usd']).quantize(Decimal('.01'), rounding=ROUND_UP)
        coins[id]["delta_price"] = (coins[id]["coin_value"] - coins[id]["avg_cost"]).quantize(Decimal('.01'), rounding=ROUND_UP)
        coins[id]["total_value"] = (coins[id]["coin_value"] * coins[id]["num_coins"]).quantize(Decimal('.01'), rounding=ROUND_UP)
        coins[id]["percent_of_cost"] = (coins[id]["total_value"] - coins[id]["total_cost"]) / coins[id]["total_cost"]

    return coins


def main():
    cursor = query_portfolio('altcoin_assets')
    coins = merge_and_average_txn_data(cursor)
    coins = query_market_data(coins)

    holdings = coins.values()

    print_header()
    print_portfolio_data(holdings)

    print_total_gains(holdings)


if __name__ == '__main__':
    main()
