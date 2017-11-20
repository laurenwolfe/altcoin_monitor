SELECT coin_name, symbol,
  (SUM(num_shares * share_price) / SUM(num_shares)) AS avg_price,
  SUM(num_shares) AS total_shares
  FROM txn_ledger
  GROUP BY coin_name, symbol;