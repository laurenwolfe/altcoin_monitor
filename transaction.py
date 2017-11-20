"""

class TxnRecord:

    def __init__(self, symbol, num_shares, share_price, storage_location, txn_time):
        self.symbol = symbol
        self.num_shares = num_shares
        self.share_price = share_price
        self.storage_location = storage_location
        self.txn_time = txn_time

    def insert_txn(self):
        # query asset table to get longform name
        # insert txn into db
"""