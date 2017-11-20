import psycopg2
import requests
from decimal import *

API_BASE = "https://api.coinmarketcap.com/v1/ticker/"


"""
def parse_current_altcoin_data(portfolio):
    total_gains = 0
    total_invested = 0
    total_worth = 0
    coin_assets = []

    for asset in portfolio:
        data = {}
        url = API_BASE + asset[0]
        coin_req = requests.get(url)
        coin_res = coin_req.json()

        data['name'] = asset[0]
        data["symbol"] = asset[1]
        data["avg_cost"] = asset[2].quantize(Decimal('.01'), rounding=ROUND_UP)
        data["num_coins"] = asset[3].quantize(Decimal('.0001'), rounding=ROUND_UP)

        data["coin_value"] = Decimal(coin_res[0]['price_usd']).quantize(Decimal('.01'), rounding=ROUND_UP)

        data["total_cost"] = (data["num_coins"] * data["avg_cost"]).quantize(Decimal('.01'), rounding=ROUND_UP)
        data["total_value"] = (data["num_coins"] * data['coin_value']).quantize(Decimal('.01'), rounding=ROUND_UP)
        data["delta_price"] = data["total_value"] - data["total_cost"]
        data["percent_of_cost"] = (data["total_value"] - data['total_cost']) / data["total_cost"]

        coin_assets.append(data)
        total_gains += data["delta_price"]
        total_invested += data["total_cost"]
        total_worth += data["total_value"]

    sorted_assets = sorted(coin_assets, key=lambda k: k["total_value"], reverse=True)

    print_header()
    print_portfolio_data(sorted_assets)
    print_total_gains(total_gains, total_invested, total_worth)
"""


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
        num_coins = str("{:,f}").format(data["num_coins"])
        avg_cost = '$ ' + str("{:,f}").format(data["avg_cost"])
        coin_value = '$ ' + str("{:,f}").format(data["coin_value"])
        diff_in_price = '$ ' + str("{:,f}").format(data["delta_price"])
        total_cost = '$ ' + str("{:,f}").format(data["total_cost"])
        total_value = '$ ' + str("{:,f}").format(data["total_value"])

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
    start_idx = 0
    curr_coin_id = 0
    holdings = []

    cursor.execute("""
    SELECT 
    co.coin_id, 
    co.coin_symbol, 
    co.coin_name, 
    t.num_shares, 
    t.share_price 
    FROM transactions as t
    JOIN coins as co ON co.coin_id = t.coin_id  ORDER BY t.coin_id;
    """)

    #  eventual todo: break into txn size limits.
    txns = cursor.fetchall()

    for curr_idx in range(0, len(txns)):
        coin_sum = Decimal(0.0)
        coin_debits = Decimal(0.0)
        coin_data = {}
        avg_cost = Decimal(0.0)

        # at the beginning, set coin_id to that of first tuple
        if curr_idx == 0:
            curr_coin_id = txns[curr_idx][0]

        # separating the debits, they'll matter after we average the cost
        if txns[curr_idx][3] > 0:
            coin_sum += txns[curr_idx][3]
        else:
            coin_debits += txns[curr_idx][3]

        #  find total qty of each coin held
        if curr_coin_id == txns[curr_idx][0]:
            continue

        # once you've run through all a currency's txns, iterate to calculate average cost per coin
        # also calculate the current balance.
        if coin_sum > 0:
            for idx in range(start_idx, curr_idx):
                if txns[idx][3] > 0:
                    cost_proportion = txns[idx][3] / coin_sum
                    avg_cost += cost_proportion * txns[idx][4]

            # Insert collected data in this coin's dictionary for later display
            coin_data["id"] = txns[start_idx][0]
            coin_data["symbol"] = txns[start_idx][1]
            coin_data["name"] = txns[start_idx][2]
            coin_data["avg_cost"] = avg_cost.quantize(Decimal('.01'), rounding=ROUND_UP)
            coin_data["num_coins"] = coin_sum + coin_debits.quantize(Decimal('.0001'), rounding=ROUND_UP)
            holdings.append(coin_data)

            # Reset the start_idx and new coin_id with the index that reached the limit
            start_idx = curr_idx
            curr_coin_id = txns[curr_idx][0]

    return holdings


def query_market_data(holdings):
    for coin in holdings:

        url = API_BASE + coin["coin_name"]
        coin_req = requests.get(url)
        coin_res = coin_req.json()

        coin["market_rate"] = coin_res[0]['price_usd'].quantize(Decimal('.01'), rounding=ROUND_UP)
        coin["coin_value"] = coin['num_coins'] * coin["market_rate"]
        coin["delta_price"] = coin["coin_value"] - coin["avg_cost"]
        coin["total_cost"] = coin["avg_cost"] * coin["num_coins"]
        coin["total_value"] = coin["coin_value"] * coin["num_coins"]
        coin["percent_of_cost"] = coin["delta_price"] / coin["total_cost"]

    return holdings


def main():
    cursor = query_portfolio('altcoin_assets')
    holdings = merge_and_average_txn_data(cursor)
    holdings = query_market_data(holdings)

    print_header()
    print_portfolio_data(holdings)
    print_total_gains(holdings)

#    parse_current_altcoin_data(cursor)


if __name__ == '__main__':
    main()
