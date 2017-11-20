import psycopg2
import requests
from decimal import *
# from asset import CoinAsset

API_BASE = "https://api.coinmarketcap.com/v1/ticker/"


def query_portfolio(db, sql):
    conn = psycopg2.connect("dbname=" + db)

    portfolio = conn.cursor()
    portfolio.execute(open(sql, 'r').read())

    return portfolio


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
        # The only way I could find to include the currency symbol directly to the left of the value,
        # while maintaining right alignment.
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


def print_total_gains(total_gains, total_invested, total_worth):
    stars = '*' * 110

    print("\n\n" + stars + "\n")
    print(" \t\t Total Gain/Loss: ${:,.2f} \t***  Total Value: ${:,.2f} \t***  Total Invested: ${:,.2f}"
          .format(total_gains, total_worth, total_invested))
    print("\n" + stars)


def main():
    portfolio = query_portfolio('altcoin_assets', 'avg.sql')

    parse_current_altcoin_data(portfolio)

if __name__ == '__main__':
    main()
