'''
class AssetPair:

    def __init__(self, symbol, base_asset, trade_asset, exchanges):
        self.symbol = symbol
        self.base_asset = base_asset
        self.trade_asset = trade_asset
        self.exchanges = exchanges


    def insert_pair(self):
        # insert pair into db, if not already exists. return id?


    def list_tradable_assets(self, symbol):
        # return list of two lists (or JSON): one where symbol is the base asset, one where it's the trade_asset.
'''
