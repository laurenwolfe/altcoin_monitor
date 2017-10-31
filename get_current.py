import psycopg2
import requests
from decimal import *

API_BASE = "https://api.coinmarketcap.com/v1/ticker/"

conn = psycopg2.connect("dbname=altcoin_assets")

portfolio = conn.cursor()
portfolio.execute(open("avg.sql", 'r').read())

data = {}
w = 22
r = 20

print('\n')
print(' Symbol'.ljust(w), '| Name'.ljust(w), '| Total Coins'.ljust(w),
      '| Per-Coin Cost'.ljust(w), '| Coin Value'.ljust(w),
    '| Capital Gain/Loss'.ljust(w), '| Percent Gain/Loss'.ljust(w))
print('-' * 162)

for asset in portfolio:
    url = API_BASE + asset[0]
    coin_req = requests.get(url)
    coin_res = coin_req.json()

    coin = {'symbol': asset[1],
            'name': asset[0],
            'shares': asset[3].quantize(Decimal('.00001'), rounding=ROUND_UP),
            'average_paid': asset[2].quantize(Decimal('.01'), rounding=ROUND_UP),
            'current_share_price': Decimal(coin_res[0]['price_usd']).quantize(Decimal('.01'), rounding=ROUND_UP),
            'purchase_price': (asset[3] * asset[2]).quantize(Decimal('.01'), rounding=ROUND_UP),
            'current_value': (asset[3] * Decimal(coin_res[0]['price_usd'])).quantize(Decimal('.01'), rounding=ROUND_UP),
            }

    coin['price_diff'] = (coin['current_value'] - coin['purchase_price']).quantize(Decimal('.01'), rounding=ROUND_UP)
    coin['percent_diff'] = (coin['purchase_price'] / coin['current_value'] * 100).quantize(Decimal('.01'), rounding=ROUND_UP)

    print(str(coin['symbol']).ljust(w), ' ', str(coin['name']).ljust(r),
          str(coin['shares']).rjust(r), str(coin['average_paid']).rjust(r),
          str(coin['current_share_price']).rjust(r), str(coin['price_diff']).rjust(r),
          str(coin['percent_diff']).rjust(r))
