# Financial Ratio Engine

## Overview

The Financial Ratio Engine is responsible for computing key financial performance indicators (KPIs) for every company-year record in the Nifty 100 Financial Intelligence Platform.

The engine combines data from the Profit & Loss Statement, Balance Sheet, Cash Flow Statement, Market Capitalization dataset, Company Master dataset, and Sector dataset to generate analytical metrics used for company screening, dashboard visualizations, and financial analysis.

All computed metrics are stored in the SQLite database and exported as supporting reports for further analysis.

---

# Objectives

The Financial Ratio Engine performs the following tasks:

- Compute profitability ratios
- Compute leverage ratios
- Compute efficiency ratios
- Compute growth (CAGR) metrics
- Compute cash flow KPIs
- Generate capital allocation patterns
- Calculate composite quality scores
- Handle financial edge cases
- Store computed KPIs in SQLite
- Generate anomaly logs for inconsistent source data

---

# Input Data Sources

The Ratio Engine uses the following datasets:

| Dataset | Purpose |
|----------|----------|
| profitandloss | Revenue, profit, operating income, EPS, dividends |
| balancesheet | Equity, reserves, borrowings, assets, liabilities |
| cashflow | Operating, investing and financing cash flow |
| market_cap | Market valuation metrics |
| companies | Company master information |
| sectors | Sector classification |

---

# Output Tables

The engine generates the following outputs:

## SQLite Tables

- financial_ratios
- company_growth_metrics

## CSV Reports

- outputs/capital_allocation.csv

## Log Files

- outputs/ratio_edge_cases.log

---

# Financial Ratios Computed

## Profitability Ratios

- Net Profit Margin
- Operating Profit Margin
- Return on Equity (ROE)
- Return on Capital Employed (ROCE)
- Return on Assets (ROA)

---

## Leverage Ratios

- Debt to Equity Ratio
- Interest Coverage Ratio
- Net Debt
- High Leverage Flag
- Interest Coverage Warning Flag

---

## Efficiency Ratios

- Asset Turnover Ratio

---

## Per Share Metrics

- Earnings Per Share (EPS)
- Book Value Per Share
- Dividend Payout Ratio

---

## Cash Flow KPIs

- Free Cash Flow
- Cash Flow Quality Score
- CapEx Intensity
- FCF Conversion Rate
- Capital Allocation Pattern

---

## Growth Metrics

The CAGR Engine computes:

- Revenue CAGR (3 Year)
- Revenue CAGR (5 Year)
- Revenue CAGR (10 Year)

- PAT CAGR (3 Year)
- PAT CAGR (5 Year)

- EPS CAGR (5 Year)

---

## Composite Quality Score

A quality score is calculated for every company using:

- Return on Equity
- Return on Capital Employed
- Revenue CAGR
- Debt to Equity Ratio

The score ranges from **0 to 100**, allowing quick comparison of overall financial quality.

---

# Formula Summary

| KPI | Formula |
|------|----------|
| Net Profit Margin | Net Profit / Sales × 100 |
| Operating Profit Margin | Operating Profit / Sales × 100 |
| Return on Equity | Net Profit / (Equity Capital + Reserves) × 100 |
| Return on Capital Employed | Operating Profit / (Equity Capital + Reserves + Borrowings) × 100 |
| Return on Assets | Net Profit / Total Assets × 100 |
| Debt to Equity | Borrowings / (Equity Capital + Reserves) |
| Interest Coverage | (Operating Profit + Other Income) / Interest |
| Net Debt | Borrowings − Investments |
| Asset Turnover | Sales / Total Assets |
| Book Value Per Share | (Equity Capital + Reserves) / Equity Capital |
| Free Cash Flow | Operating Cash Flow + Investing Cash Flow |

---

# CAGR Edge Case Handling

The CAGR engine handles the following scenarios:

| Situation | Behaviour |
|------------|-----------|
| Positive to Positive | CAGR calculated normally |
| Positive to Negative | DECLINE_TO_LOSS |
| Negative to Positive | TURNAROUND |
| Negative to Negative | BOTH_NEGATIVE |
| Zero Base Value | ZERO_BASE |
| Insufficient Historical Data | INSUFFICIENT |

Each CAGR value is stored together with its corresponding status flag.

---

# Capital Allocation Patterns

The engine classifies every company-year into one of the following patterns based on Operating, Investing and Financing Cash Flows.

Examples include:

- Reinvestor
- Shareholder Returns
- Growth Funded by Debt
- Cash Accumulator
- Mixed
- Distress Signal
- Asset Liquidation
- Pre-Revenue

The results are exported to:

```
outputs/capital_allocation.csv
```

---

# Edge Case Handling

The Ratio Engine includes built-in safeguards for invalid financial situations.

Examples include:

- Division by zero returns NULL
- Negative equity returns NULL for ROE
- Debt-free companies return Debt Free for Interest Coverage Label
- Financial sector companies are excluded from Debt-to-Equity warning flags
- Missing historical data prevents CAGR calculation
- Invalid financial values are logged automatically

---

# Ratio Validation

During execution, calculated ratios are compared against selected values supplied in the source datasets.

Examples include:

- Operating Profit Margin
- Return on Equity
- Return on Capital Employed

Any significant differences are recorded in:

```
outputs/ratio_edge_cases.log
```

These discrepancies are documented for review and do not interrupt execution.

---

# Data Quality Notes

The source datasets are provided by the organization.

During validation, a small number of inconsistencies were observed between the supplied ratio values and the ratios calculated directly from the raw financial statements.

Following the project requirements:

- Calculated ratio values are used for analytical purposes.
- Source ratio values are retained for reference and comparison.
- All discrepancies are documented in the anomaly log rather than modifying the original source data.

This ensures complete transparency while preserving data integrity.

---

# Files Implemented

The Financial Ratio Engine consists of the following modules:

```
src/
└── analytics/
    ├── ratio_engine.py
    ├── ratios.py
    ├── cagr.py
    ├── cashflow_kpis.py
    ├── edge_case_logger.py
    └── save_results.py
```

---

# Deliverables

The completed Ratio Engine provides:

- Automated computation of financial KPIs
- Company growth metrics
- Cash flow analytics
- Composite quality scoring
- Capital allocation analysis
- SQLite database integration
- CSV report generation
- Automated anomaly logging

These outputs serve as the analytical foundation for the Financial Intelligence Platform dashboard and company screening modules.