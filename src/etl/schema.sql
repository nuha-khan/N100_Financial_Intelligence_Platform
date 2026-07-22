PRAGMA foreign_keys = ON;

----------------------------------------------------
-- Companies
----------------------------------------------------

CREATE TABLE IF NOT EXISTS companies (

    id TEXT PRIMARY KEY,

    company_logo TEXT,
    company_name TEXT,
    chart_link TEXT,
    about_company TEXT,

    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,

    face_value REAL,
    book_value REAL,

    roce_percentage REAL,
    roe_percentage REAL
);

----------------------------------------------------
-- Analysis
----------------------------------------------------

CREATE TABLE IF NOT EXISTS analysis (

    id INTEGER PRIMARY KEY,

    company_id TEXT,

    compounded_sales_growth REAL,
    compounded_profit_growth REAL,
    stock_price_cagr REAL,
    roe REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Profit & Loss
----------------------------------------------------

CREATE TABLE IF NOT EXISTS profitandloss (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    sales REAL,
    expenses REAL,

    operating_profit REAL,
    opm_percentage REAL,

    other_income REAL,
    interest REAL,
    depreciation REAL,

    profit_before_tax REAL,
    tax_percentage REAL,

    net_profit REAL,

    eps REAL,
    dividend_payout REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Balance Sheet
----------------------------------------------------

CREATE TABLE IF NOT EXISTS balancesheet (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    equity_capital REAL,
    reserves REAL,

    borrowings REAL,
    other_liabilities REAL,

    total_liabilities REAL,

    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,

    total_assets REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Cash Flow
----------------------------------------------------

CREATE TABLE IF NOT EXISTS cashflow (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,

    net_cash_flow REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Documents
----------------------------------------------------

CREATE TABLE IF NOT EXISTS documents (

    id INTEGER PRIMARY KEY,

    company_id TEXT,

    year INTEGER,

    Annual_Report TEXT,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Pros & Cons
----------------------------------------------------

CREATE TABLE IF NOT EXISTS prosandcons (

    id INTEGER PRIMARY KEY,

    company_id TEXT,

    pros TEXT,
    cons TEXT,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Market Cap
----------------------------------------------------

CREATE TABLE IF NOT EXISTS market_cap (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    market_cap_crore REAL,
    enterprise_value_crore REAL,

    pe_ratio REAL,
    pb_ratio REAL,

    ev_ebitda REAL,
    dividend_yield_pct REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Sectors
----------------------------------------------------

CREATE TABLE IF NOT EXISTS sectors (

    id INTEGER PRIMARY KEY,

    company_id TEXT,

    broad_sector TEXT,
    sub_sector TEXT,

    index_weight_pct REAL,

    market_cap_category TEXT,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Stock Prices
----------------------------------------------------

CREATE TABLE IF NOT EXISTS stock_prices (

    id INTEGER PRIMARY KEY,

    company_id TEXT,

    date DATE,

    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,

    volume INTEGER,

    adjusted_close REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Financial Ratios
----------------------------------------------------

CREATE TABLE IF NOT EXISTS financial_ratios (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,

    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,

    free_cash_flow_cr REAL,
    capex_cr REAL,

    earnings_per_share REAL,
    book_value_per_share REAL,

    dividend_payout_ratio_pct REAL,

    total_debt_cr REAL,
    cash_from_operations_cr REAL,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Peer Groups
----------------------------------------------------

CREATE TABLE IF NOT EXISTS peer_groups (

    id INTEGER PRIMARY KEY,

    peer_group_name TEXT,

    company_id TEXT,

    is_benchmark TEXT,

    FOREIGN KEY(company_id)
    REFERENCES companies(id)
);

----------------------------------------------------
-- Indexes
----------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_analysis_company
ON analysis(company_id);

CREATE INDEX IF NOT EXISTS idx_profit_company
ON profitandloss(company_id);

CREATE INDEX IF NOT EXISTS idx_profit_year
ON profitandloss(year);

CREATE INDEX IF NOT EXISTS idx_bs_company
ON balancesheet(company_id);

CREATE INDEX IF NOT EXISTS idx_bs_year
ON balancesheet(year);

CREATE INDEX IF NOT EXISTS idx_cf_company
ON cashflow(company_id);

CREATE INDEX IF NOT EXISTS idx_cf_year
ON cashflow(year);

CREATE INDEX IF NOT EXISTS idx_doc_company
ON documents(company_id);

CREATE INDEX IF NOT EXISTS idx_doc_year
ON documents(year);

CREATE INDEX IF NOT EXISTS idx_market_company
ON market_cap(company_id);

CREATE INDEX IF NOT EXISTS idx_market_year
ON market_cap(year);

CREATE INDEX IF NOT EXISTS idx_sector_company
ON sectors(company_id);

CREATE INDEX IF NOT EXISTS idx_stock_company
ON stock_prices(company_id);

CREATE INDEX IF NOT EXISTS idx_stock_date
ON stock_prices(date);

CREATE INDEX IF NOT EXISTS idx_ratio_company
ON financial_ratios(company_id);

CREATE INDEX IF NOT EXISTS idx_ratio_year
ON financial_ratios(year);

CREATE INDEX IF NOT EXISTS idx_peer_company
ON peer_groups(company_id);

CREATE INDEX IF NOT EXISTS idx_peer_group
ON peer_groups(peer_group_name);