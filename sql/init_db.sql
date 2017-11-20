CREATE TABLE coins (
  coin_id       SERIAL PRIMARY KEY,
  coin_name     VARCHAR(50) NOT NULL,
  coin_symbol   VARCHAR(6) NOT NULL
);

CREATE TABLE wallets (
  wallet_id           SERIAL PRIMARY KEY,
  wallet_name         VARCHAR(50) NOT NULL,
  wallet_description  VARCHAR(255)
);

CREATE TABLE transactions (
  coin_id           INTEGER NOT NULL,
  wallet_id         INTEGER NOT NULL,
  num_shares        DECIMAL NOT NULL,
  share_price       DECIMAL,
  txn_time          TIMESTAMP DEFAULT now()
);