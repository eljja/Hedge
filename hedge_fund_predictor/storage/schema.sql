CREATE TABLE IF NOT EXISTS fund_universe (
    fund_group TEXT,
    cik TEXT,
    strategy TEXT,
    aum_thousands BIGINT,
    public_vehicle TEXT,
    last_updated TIMESTAMP,
    PRIMARY KEY (fund_group, cik)
);

CREATE TABLE IF NOT EXISTS holdings_13f (
    cik TEXT,
    report_date DATE,
    filing_date DATE,
    cusip TEXT,
    issuer TEXT,
    class_title TEXT,
    value_thousands BIGINT,
    shares_or_amount BIGINT,
    shares_type TEXT,
    put_call TEXT DEFAULT 'NONE',
    investment_discretion TEXT,
    is_amendment BOOLEAN DEFAULT FALSE,
    is_ct_revealed BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (cik, report_date, cusip, class_title)
);

CREATE INDEX IF NOT EXISTS idx_holdings_cik_date ON holdings_13f (cik, report_date);
CREATE INDEX IF NOT EXISTS idx_holdings_cusip ON holdings_13f (cusip);

CREATE TABLE IF NOT EXISTS filings_metadata (
    cik TEXT,
    form_type TEXT,
    filing_date DATE,
    accession_number TEXT,
    primary_doc TEXT,
    filing_delay_days INT,
    PRIMARY KEY (cik, accession_number)
);

CREATE TABLE IF NOT EXISTS market_prices (
    ticker TEXT,
    date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    adj_close DOUBLE,
    volume BIGINT,
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_market_prices_date ON market_prices (date);

CREATE TABLE IF NOT EXISTS sector_etf_returns (
    date DATE,
    XLK DOUBLE,
    XLF DOUBLE,
    XLE DOUBLE,
    XLV DOUBLE,
    XLY DOUBLE,
    XLP DOUBLE,
    XLI DOUBLE,
    XLC DOUBLE,
    XLB DOUBLE,
    XLU DOUBLE,
    XLRE DOUBLE,
    SMH DOUBLE,
    ICLN DOUBLE,
    BITO DOUBLE,
    TLT DOUBLE,
    GLD DOUBLE,
    UUP DOUBLE,
    PRIMARY KEY (date)
);

CREATE TABLE IF NOT EXISTS ff_factors_daily (
    date DATE,
    mkt_rf DOUBLE,
    smb DOUBLE,
    hml DOUBLE,
    rmw DOUBLE,
    cma DOUBLE,
    rf DOUBLE,
    PRIMARY KEY (date)
);

CREATE TABLE IF NOT EXISTS cftc_cot (
    report_date DATE,
    market_name TEXT,
    contract_type TEXT,
    lev_long BIGINT,
    lev_short BIGINT,
    lev_net BIGINT,
    mm_long BIGINT,
    mm_short BIGINT,
    mm_net BIGINT,
    z_score DOUBLE,
    PRIMARY KEY (report_date, market_name, contract_type)
);

CREATE TABLE IF NOT EXISTS fund_nav (
    fund_group TEXT,
    date DATE,
    nav DOUBLE,
    source TEXT,
    PRIMARY KEY (fund_group, date)
);

CREATE TABLE IF NOT EXISTS events_realtime (
    cik TEXT,
    event_type TEXT,
    event_date DATE,
    ticker TEXT,
    cusip TEXT,
    shares BIGINT,
    value_thousands BIGINT,
    direction TEXT,
    raw_json TEXT,
    PRIMARY KEY (cik, event_type, event_date, cusip)
);

CREATE TABLE IF NOT EXISTS position_estimates (
    fund_group TEXT,
    estimate_date DATE,
    sector TEXT,
    estimated_weight DOUBLE,
    confidence_score DOUBLE,
    engine_source TEXT,
    ticker TEXT,
    PRIMARY KEY (fund_group, estimate_date, ticker, engine_source)
);
