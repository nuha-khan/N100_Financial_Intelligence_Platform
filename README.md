# N100 Financial Intelligence Platform

A Python-based financial analytics platform for the Nifty 100 index that transforms raw financial statements into structured analytics using automated ETL pipelines, financial ratio computation, screening models, and peer comparison analysis.

> 🚧 **Status:** Sprint 3 – Peer Comparison Engine (Day 18 Completed)

---

# Features

- Automated ETL pipeline for 12 financial datasets
- Data normalization and validation using 16 Data Quality rules
- SQLite data warehouse
- Financial Ratio Engine (50+ KPIs)
- CAGR Engine with edge-case handling
- Cash Flow & Capital Allocation Analysis
- Composite Quality Scoring
- Configurable Financial Screener
- Peer Comparison Engine
- Sector-aware analytics
- Automated reports and audit generation

---

# Tech Stack

- Python
- Pandas
- NumPy
- SQLite
- OpenPyXL
- PyYAML

---

# Project Structure

```text
N100_Financial_Intelligence_Platform/
│
├── config/
│   └── screener_config.yaml
│
├── data/
│
├── outputs/
│   ├── validation_failures.csv
│   ├── load_audit.csv
│   ├── capital_allocation.csv
│   ├── ratio_edge_cases.log
│   └── screener_output.xlsx
│
├── reports/
│   └── radar_charts/
│
├── src/
│   ├── etl/
│   ├── analytics/
│   └── screener/
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

# Implemented Modules

## Sprint 1 — Data Foundation

- Excel Loader
- Data Normalization
- SQLite Schema
- SQLite Loader
- Data Validation Engine
- 16 Data Quality Rules
- Validation Reports
- Load Audit Generation

---

## Sprint 2 — Financial Ratio Engine

Implemented:

- Profitability Ratios
  - Net Profit Margin
  - Operating Profit Margin
  - Return on Equity (ROE)
  - Return on Capital Employed (ROCE)
  - Return on Assets (ROA)

- Leverage & Efficiency Ratios
  - Debt-to-Equity
  - Interest Coverage Ratio
  - Net Debt
  - Asset Turnover

- CAGR Engine
  - Revenue CAGR
  - PAT CAGR
  - EPS CAGR
  - Complete edge-case handling

- Cash Flow Analytics
  - Free Cash Flow
  - CapEx Intensity
  - FCF Conversion
  - Capital Allocation Pattern Classification

- Financial Ratio Engine
- Company Growth Metrics
- Capital Allocation Report
- SQLite Integration

---

## Sprint 3 — Screener & Peer Comparison

Completed

### Financial Screener

- Configurable YAML-based screening engine
- 6 Investment Presets
  - Quality Compounder
  - Value Pick
  - Growth Accelerator
  - Dividend Champion
  - Debt-Free Blue Chip
  - Turnaround Watch

- Sector-aware filtering
- Composite Quality Score integration
- Screener report generation

### Peer Comparison

- Peer group mapping
- Percentile ranking across peer groups
- 10 financial metric comparisons
- SQLite peer_percentiles table generation

---

# Current Progress

| Module | Status |
|---------|--------|
| ETL Pipeline | ✅ Completed |
| Data Normalization | ✅ Completed |
| Data Validation | ✅ Completed |
| SQLite Integration | ✅ Completed |
| Financial Ratio Engine | ✅ Completed |
| CAGR Engine | ✅ Completed |
| Cash Flow Analytics | ✅ Completed |
| Composite Quality Scoring | ✅ Completed |
| Financial Screener | ✅ Completed |
| Peer Comparison Engine | ✅ Completed (Day 18) |
| Radar Chart Generator | 🚧 In Progress |
| Peer Comparison Reports | ⏳ Pending |

---

# Generated Outputs

- `validation_failures.csv`
- `load_audit.csv`
- `capital_allocation.csv`
- `ratio_edge_cases.log`
- `screener_output.xlsx`

---

# Database Tables

The SQLite warehouse currently contains structured financial data including:

- companies
- profitandloss
- balancesheet
- cashflow
- market_cap
- sectors
- peer_groups
- financial_ratios
- company_growth_metrics
- peer_percentiles

---

# Data

This project processes financial data from multiple Excel sources.

> **Note:** The original datasets are not included in this repository as they were provided as part of an internship project and are confidential.

Place the datasets inside:

```text
data/raw/
data/supporting/
```

The ETL pipeline automatically discovers and processes all supported files.

---

# Run

```bash
# ETL
python -m src.etl.loader

# Validation
python -m src.etl.validator

# Financial Ratio Engine
python -m src.analytics.ratio_engine

# Financial Screener
python -m src.screener.engine

# Peer Comparison
python -m src.analytics.peer
```

---

# Upcoming Work

- Radar Chart Generator
- Peer Comparison Excel Report
- Interactive Dashboard
- Final Reporting

---

# Author

**Nuha AjmalKhan Pathan**

Data Analyst Intern @ Bluestock Fintech
