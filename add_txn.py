"""
 todo: allow bulk insertion via csv; output data via keyboard commands
"""
import psycopg2
from datetime import datetime


def insert_new_coin(symbol, cursor):
    """ Inserts a new currency into the database, if it doesn't already exist.

    :param symbol: abbreviated name for the currency
    :type symbol: string
    :param cursor: database control structure for allowing SQL execution
    :type cursor: cursor
    :return: The new coin_id, -1 in case of error
    :rtype: int
    """
    name = input("What is the full name of the coin with symbol {}? ".format(symbol))
    while name is None:
        name = input("A name is required to enter a new coin. Please input it now: ")
    name = str(name)

    try:
        # noinspection SyntaxError
        cursor.execute("INSERT INTO coins (coin_name, coin_symbol) VALUES (%s, %s)", (name, symbol))
    except psycopg2.Error as e:
        print(e.pgerror)
        return -1

    # noinspection SyntaxError,SyntaxError
    cursor.execute("SELECT * FROM coins WHERE coin_symbol = %s AND coin_name = %s", (symbol, name))
    res = cursor.fetchone()
    return res[0]


def insert_new_wallet(wallet_name, cursor):
    """Generates an entry for new storage location.

    :param wallet_name: location where coins are being stored
    :type wallet_name: string
    :param cursor: database cursor
    :type cursor: cursor
    :return: the new wallet_id
    :rtype: int
    """
    wallet_desc = input("Please enter a description for {} (press return to skip): ".format(wallet_name))
    if wallet_desc is None:
        wallet_desc = "NULL"
    wallet_desc = str(wallet_desc)

    #  inserts new wallet row and returns id from database
    try:
        # noinspection SyntaxError,SyntaxError
        cursor.execute("""
        INSERT INTO wallets (wallet_name, wallet_description) VALUES (%s, %s)
        """, (wallet_name, wallet_desc))
    except psycopg2.Error as e:
        print(e.pgerror)

    # noinspection SyntaxError,SyntaxError
    cursor.execute("""
    SELECT * FROM wallets 
    WHERE wallet_name = %s AND wallet_description = %s
    """, (wallet_name, wallet_desc))

    res = cursor.fetchone()
    return res[0]


def get_coin_id(symbol, cursor):
    """ Retrieves coin_id for previously-seen currencies

    :param symbol: 3/4 letter code identifying coin
    :type symbol: string
    :param cursor: db structure
    :type cursor: cursor
    :return: coin_id for the given currency
    :rtype: int
    """
    # noinspection SyntaxError
    cursor.execute("SELECT coin_id FROM coins WHERE coin_symbol = %s",
                   (symbol,))
    res = cursor.fetchone()

    if res is None:
        return insert_new_coin(symbol, cursor)
    return res[0]


def get_wallet_id(wallet_name, cursor):
    # noinspection SyntaxError
    """ Retrieves wallet_id for existing storage locations.

    :param wallet_name: identifier for storage of currency
    :type wallet_name: string
    :param cursor: db structure
    :type cursor: cursor
    :return: existing wallet_id
    :rtype: int
    """
    # noinspection SyntaxError
    cursor.execute("SELECT wallet_id FROM wallets WHERE wallet_name = %s",
                   (wallet_name,))
    res = cursor.fetchone()

    if res is None:
        return insert_new_wallet(wallet_name, cursor)
    return res[0]


def get_txn_data():
    """ Prompts user to input txn data via keyboard entries

    :return: dictionary of inputted dated
    :rtype: dictionary
    """
    txn_data = {}

    #  the 3-4 letter abbreviation for the coin
    coin_symbol = input("Please enter the coin's symbol: ")
    while coin_symbol is None:
        coin_symbol = input("The coin's symbol is required. Please enter it now: ")
    txn_data["coin_symbol"] = str(coin_symbol)

    #  negative to exchange crypto into another form of currency
    shares = input("Please enter the number of shares to credit or debit: ")
    while shares is None:
        shares = input("No input. Please enter the number of shares acquired now: ")
    txn_data["shares"] = float(shares)

    #  disregarding useless txns
    if txn_data["shares"] == 0:
        print("Thank you. No further data is required for a transaction without credit or debit of coins.")
        exit(0)
    elif txn_data["shares"] < 0:
        txn_data["price"] = None
    else:
        #  trading price of coin is only required for buys. Sells don't change the average purchase cost of coins.
        price = input("What was the coin price at the time of acquisition: ")
        while price is None or str(price).isalpha() or float(price) < 0:
            price = input("A valid coin price is required (not negative or blank--$0 does work). Please enter it now: ")
        txn_data["price"] = float(price)

    # possible todo -- output list of current wallets
    wallet_name = input("Please specify the wallet location where the coins are being stored: ")
    while wallet_name is None:
        wallet_name = input("The wallet name is required. Please enter it now: ")
    txn_data["wallet_name"] = str(wallet_name)

    time = input("Please input the date of the transaction as follows, \"YYYY-MM-DD\" (press return for today): ")
    if time is None:
        txn_data["time"] = None
    else:
        txn_data["time"] = str(time)
    return txn_data


def print_wallet_names(cursor):
    """ Outputs a list of names and ids for existing wallets, to aid in data entry.

    :param cursor: db control structure
    :type cursor: cursor
    """
    cursor.execute("SELECT wallet_id, wallet_name FROM wallets ORDER BY wallet_name")

    wallets = cursor.fetchall()

    for wallet in wallets:
        print("{:d}- {}".format(wallet[0], wallet[1]))


def input_txn(txn, cursor):
    """ Inserts new transaction data into the database.

    :param txn: dictionary of transaction metadata
    :type txn: dict
    :param cursor: db control structure
    :type cursor: cursor
    """
    coin_id = get_coin_id(txn["coin_symbol"], cursor)
    wallet_id = get_wallet_id(txn["wallet_name"], cursor)

    if txn["time"] is None:
        txn["time"] = datetime.now()
    else:
        txn["time"] = datetime.strptime(txn["time"], "%Y-%m-%d")

    if txn["price"] is None or float(txn["price"]) <= 0.0:
        # noinspection SyntaxError,SyntaxError,SyntaxError,SyntaxError
        cursor.execute("""
              INSERT INTO transactions 
              (coin_id, wallet_id, num_shares, txn_time)
              VALUES (%s, %s, %s, %s)
              """, (coin_id, wallet_id, txn["shares"], txn["time"]))
    else:
        # noinspection SyntaxError,SyntaxError,SyntaxError,SyntaxError,SyntaxError
        cursor.execute("""
              INSERT INTO transactions 
              (coin_id, wallet_id, num_shares, share_price, txn_time)
              VALUES (%s, %s, %s, %s, %s)
              """, (coin_id, wallet_id, txn["shares"], txn["price"], txn["time"]))


# noinspection SpellCheckingInspection
def main():
    """
        This file handles the collection and storage (in postgres db) of cryptocurrency transaction data.
    """
    conn = psycopg2.connect("dbname=altcoin_assets")
    cursor = conn.cursor()
    txn = get_txn_data()
    input_txn(txn, cursor)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
