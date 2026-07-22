-- ============================================================
-- N100 Financial Intelligence Platform
-- Exploratory SQL Queries
-- ============================================================

------------------------------------------------------------
-- Query 1 : Total records in each table
------------------------------------------------------------

SELECT 'companies' AS table_name, COUNT(*) AS total_rows FROM companies
UNION ALL
SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL
SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices;

------------------------------------------------------------
-- Query 2 : Top 10 companies by latest Market Capitalization
------------------------------------------------------------

SELECT
    company_id,
    year,
    market_cap_crore
FROM market_cap
ORDER BY market_cap_crore DESC
LIMIT 10;

------------------------------------------------------------
-- Query 3 : Top 10 companies by latest Net Profit
------------------------------------------------------------

SELECT
    company_id,
    year,
    net_profit
FROM profitandloss
ORDER BY net_profit DESC
LIMIT 10;

------------------------------------------------------------
-- Query 4 : Companies with Negative Net Profit
------------------------------------------------------------

SELECT
    company_id,
    year,
    net_profit
FROM profitandloss
WHERE net_profit < 0
ORDER BY net_profit;

------------------------------------------------------------
-- Query 5 : Companies having fewer than 5 years of data
------------------------------------------------------------

SELECT
    company_id,
    COUNT(DISTINCT year) AS years_available
FROM profitandloss
GROUP BY company_id
HAVING COUNT(DISTINCT year) < 5
ORDER BY years_available;

------------------------------------------------------------
-- Query 6 : Number of companies in each Broad Sector
------------------------------------------------------------

SELECT
    broad_sector,
    COUNT(*) AS companies
FROM sectors
GROUP BY broad_sector
ORDER BY companies DESC;

------------------------------------------------------------
-- Query 7 : Average ROE by Sector
------------------------------------------------------------

SELECT
    s.broad_sector,
    ROUND(AVG(c.roe_percentage),2) AS average_roe
FROM companies c
JOIN sectors s
ON c.id = s.company_id
GROUP BY s.broad_sector
ORDER BY average_roe DESC;

------------------------------------------------------------
-- Query 8 : Highest Operating Profit Margin
------------------------------------------------------------

SELECT
    company_id,
    year,
    opm_percentage
FROM profitandloss
ORDER BY opm_percentage DESC
LIMIT 10;

------------------------------------------------------------
-- Query 9 : Companies with Highest Debt
------------------------------------------------------------

SELECT
    company_id,
    year,
    borrowings
FROM balancesheet
ORDER BY borrowings DESC
LIMIT 10;

------------------------------------------------------------
-- Query 10 : Latest Closing Price of each Company
------------------------------------------------------------

SELECT
    company_id,
    MAX(date) AS latest_date,
    adjusted_close
FROM stock_prices
GROUP BY company_id
ORDER BY company_id;