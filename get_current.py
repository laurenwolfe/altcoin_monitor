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


def merge_and_average_txn_data(cursor):
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

        txn_per_coin_cost = txns[i][4]
        txn_shares = txns[i][3]
        txn_total = txn_per_coin_cost * txn_shares

        if coin_id not in coins:
            coins[coin_id] = {}
            coins[coin_id]['coin_id'] = coin_id
            coins[coin_id]['symbol'] = txns[i][1]
            coins[coin_id]['coin_name'] = txns[i][2]
            coins[coin_id]['num_shares'] = txn_shares
            coins[coin_id]['total_cost'] = txn_total
            coins[coin_id]['avg_cost'] = 0
            coins[coin_id]['sum_shares'] = 0
            coins[coin_id]['sum_cost'] = 0
            coins[coin_id]['fiat_profit'] = 0
        else:
            coins[coin_id]['num_shares'] += txn_shares
            coins[coin_id]['total_cost'] += txn_total

        if txn_shares > 0 and txn_total > 0:
            coins[coin_id]['sum_cost'] += txn_total
            coins[coin_id]['sum_shares'] += txn_shares

    for coin_id in coins:
        if 'sum_shares' in coins[coin_id] and coins[coin_id]['sum_shares'] > 0:
            coins[coin_id]['avg_cost'] = coins[coin_id]['sum_cost'] / coins[coin_id]['sum_shares']
    return coins


def poll_api(url):
    coin_req = requests.get(url)
    return coin_req.json()


def query_market_data(coins):
    for cid in coins:
        coins[cid]['total_value'] = Decimal(0.0).quantize(Decimal('.01'), rounding=ROUND_UP)
        coins[cid]['coin_value'] = 0.0
        coins[cid]['percent_of_cost'] = 0.0

        url = API_BASE + coins[cid]["coin_name"]
        coin_res = poll_api(url)

        if 'error' in coin_res:
            continue

        price = Decimal(coin_res[0]['price_usd']).quantize(Decimal('.01'), rounding=ROUND_UP)

        if coins[cid]['num_shares'] > 0:
            coins[cid]['coin_value'] = price
            coins[cid]['total_value'] = price * Decimal(coins[cid]["num_shares"])\
                .quantize(Decimal('.01'), rounding=ROUND_UP)
            purchase_cost = Decimal(coins[cid]['sum_cost']).quantize(Decimal('.01'), rounding=ROUND_UP)
            total_value = Decimal(coins[cid]['total_value']).quantize(Decimal('.01'), rounding=ROUND_UP)
            coins[cid]['percent_of_cost'] = purchase_cost / total_value
            profits = total_value - purchase_cost
            coins[cid]['fiat_profit'] = profits

    return coins


def print_header():
    print()
    print('Symbol'.ljust(8),
          '| Exchange Rate '.ljust(19),
          '| Averaged Coin Price'.ljust(21),
          '| P/L Percentage'.ljust(17),
          '| Current Total Value'.ljust(20),
          '| Profit/Loss'.ljust(20),
          '| Number of Coins Owned'.ljust(19),
          '| Total Investment'.ljust(21))


def print_portfolio_data(sorted_assets):
    for data in sorted_assets:
        if data["num_shares"] > 0 and data["coin_value"] > 0:
            # This separation allowed the figures to right justify while still appending a dollar sign to the front.
            num_coins = str("{:,.4f}").format(data["num_shares"])
            avg_cost = '$ ' + str("{:,.2f}").format(data["avg_cost"])
            coin_value = '$ ' + str("{:,.2f}").format(data["coin_value"])
            total_value = '$ ' + str("{:,.2f}").format(data["total_value"])
            sum_cost = '$ ' + str("{:,.2f}").format(data["sum_cost"])
            fiat_profit = '$ ' + str("{:,.2f}").format(data["fiat_profit"])

            print('-' * 165)
            print(" {:<11} {:>16} {:>20} {:>17.2%} {:>20} {:>19} {:>21} {:>23}".format(
                data["symbol"],
                coin_value,
                avg_cost,
                data["percent_of_cost"],
                total_value,
                fiat_profit,
                num_coins,
                sum_cost))


def print_total_gains(holdings):
    total_invested = Decimal(0.0)
    total_value = Decimal(0.0)
    total_profit = Decimal(0.0)

    for coin in holdings:
        if coin['num_shares'] > 0:
            total_invested += Decimal(coin["total_cost"]).quantize(Decimal('.01'), rounding=ROUND_UP)
            total_value += Decimal(coin["total_value"]).quantize(Decimal('.01'), rounding=ROUND_UP)

            total_profit += total_value - total_invested
    stars = '*' * 110
    print("\n\n" + stars + "\n")
    print(" \t\t Total Value: ${:,.2f} \t*** Total Gain/Loss: ${:,.2f} \t***  Total Invested: ${:,.2f}"
          .format(total_value, total_profit, total_invested))
    print("\n" + stars)


def main():
    cursor = query_portfolio('altcoin_assets')
    coins = merge_and_average_txn_data(cursor)
    coins = query_market_data(coins)

    holdings = list(coins.values())
    holdings_sorted = sorted(holdings, key=itemgetter('total_value'), reverse=True)
    print_header()
    print_portfolio_data(holdings_sorted)
    print_total_gains(holdings)


if __name__ == '__main__':
    main()
