import psycopg2
import requests
from decimal import *
from types import *
from operator import itemgetter

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
        if data["num_shares"] > 0 and data["coin_value"] > 0:
            # This separation allowed the figures to right justify while still appending a dollar sign to the front.
            num_coins = str("{:,.4f}").format(data["num_shares"])
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

        if coin_id not in sums and txns[i][3] > 0:
            sums[coin_id] = txns[i][3]
            coins[coin_id] = {}
            coins[coin_id]['coin_id'] = txns[i][0]
            coins[coin_id]['symbol'] = txns[i][1]
            coins[coin_id]['coin_name'] = txns[i][2]
            coins[coin_id]['avg_cost'] = txns[i][4]
            coins[coin_id]['total_cost'] = txns[i][3] * txns[i][4]
            coins[coin_id]['num_shares'] = txns[i][3]
            coins[coin_id]['coin_value'] = 0.0
            coins[coin_id]['delta_price'] = 0
            coins[coin_id]['total_value'] = 0
            coins[coin_id]['percent_of_cost'] = 0
        else:
            sums[coin_id] += txns[i][3]
            coins[coin_id]['num_shares'] += txns[i][3]
            coins[coin_id]['total_cost'] += txns[i][3] * txns[i][4]
    

    # Calculate average cost per coin held
    for i in coins.keys():
        if coins[i]['num_shares'] > 0:
            coins[i]['avg_cost'] = (Decimal(coins[i]['total_cost']) / Decimal(coins[i]['num_shares']))
    return coins


def poll_api(url):
    coin_req = requests.get(url)
    return coin_req.json()


def query_market_data(coins):
    for cid in coins.keys():
        url = API_BASE + coins[cid]["coin_name"]
        coin_res = poll_api(url)

        if isinstance(coin_res, list):
            #  also contains % change over 1h, 24h, 7d, market cap, volume over 24 hours, rank
            price = Decimal(coin_res[0]['price_usd']).quantize(Decimal('.01'), rounding=ROUND_UP)
            if coins[cid]['num_shares'] > 0:
                coins[cid]['coin_value'] = price
                coins[cid]['total_value'] = price * Decimal(coins[cid]["num_shares"])\
                    .quantize(Decimal('.01'), rounding=ROUND_UP)

                coins[cid]['delta_price'] = (coins[cid]["total_value"] - coins[cid]["total_cost"])\
                    .quantize(Decimal('.01'), rounding=ROUND_UP)

                coins[cid]["percent_of_cost"] = \
                    (coins[cid]["total_value"] - coins[cid]["total_cost"]) / coins[cid]["total_cost"]
    return coins


def main():
    cursor = query_portfolio('altcoin_assets')
    coins = merge_and_average_txn_data(cursor)

    coins = query_market_data(coins)
    holdings = list(coins.values())
    print(holdings)
    holdings_sorted = sorted(holdings, key=itemgetter('total_value'), reverse=True)
    print_header()
    print_portfolio_data(holdings_sorted)
    print_total_gains(holdings)


if __name__ == '__main__':
    main()
