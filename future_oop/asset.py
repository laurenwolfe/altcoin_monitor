"""
class CoinAsset:
    def __init__(self, data):
        self.name = data['name']
        self.symbol = data['symbol']
        # self.age = data['age']
        # self.trade_pairs = []
        # self.exchanges = []
        self.coins_owned = data["num_coins"]
        self.avg_cost = data["avg_cost"]
        self.buy_order_price = 0
        self.sell_order_price = 0
        # self.open_price = data['open_price']
        # self.close_price = data['close_price']
        # self.high_price = data['high_price']
        # self.low_price = data['low_price']
        # self.trade_volume = data['trade_volume']
        # self.market_cap = data['market_cap']
        # self.txn_fee = data['txn_fee']
        # self.mempool_size = data['mempool_size']


    def insert_asset(self):
        # name, symbol, age


    def set_sell_order(self, sell_price):
        self.sell_order_price = sell_price

        if self.coins_owned <= 0:
            print("Sell order price set, but no coin balance found.")
        else:
            print("Sell order price set.")


    def set_buy_order(self, buy_price):
        self.buy_order_price = buy_price
        print("Buy order price set.")

"""