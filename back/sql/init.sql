CREATE TABLE IF NOT EXISTS crypto_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL NOT NULL,
    volume_24h DECIMAL NOT NULL,
    market_cap DECIMAL NOT NULL,
    percent_change_1h DECIMAL,
    percent_change_24h DECIMAL,
    percent_change_7d DECIMAL,
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL
);

CREATE INDEX idx_crypto_symbol_timestamp ON crypto_prices(symbol, timestamp);

CREATE TABLE IF NOT EXISTS crypto_aggregates (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open_price DECIMAL NOT NULL,
    high_price DECIMAL NOT NULL,
    low_price DECIMAL NOT NULL,
    close_price DECIMAL NOT NULL,
    volume DECIMAL NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE INDEX idx_crypto_agg_symbol_timeframe ON crypto_aggregates(symbol, timeframe, timestamp);
