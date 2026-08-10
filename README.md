# N100 Financial Intelligence Platform

A Python-based financial analytics platform for the Nifty 100 index that transforms raw financial statements into structured analytics using automated ETL pipelines, financial ratios, screening models, peer comparison, valuation analytics, and an interactive Streamlit dashboard.

> ✅ **Status:** Sprint 4 Completed — Dashboard & Valuation Module

---

## Features

- Automated ETL pipeline for 12 financial datasets
- Data normalization and 16 Data Quality rules
- SQLite financial data warehouse
- 50+ financial KPIs and ratio analysis
- Revenue, PAT and EPS CAGR analysis
- Free Cash Flow and CapEx analytics
- Capital allocation classification
- Composite quality scoring
- Configurable financial screener with 6 presets
- Peer comparison and radar analysis
- Sector and trend analysis
- 8-screen interactive Streamlit dashboard
- Valuation analysis with FCF Yield and P/E flags
- CSV and Excel exports
- Automated validation and reporting

---

## Tech Stack

### Languages & Libraries

- Python
- Pandas
- NumPy
- SQLite
- OpenPyXL
- Plotly
- Streamlit
- PyYAML

### Tools

- Git
- GitHub
- VS Code

---

## Project Structure

N100_Financial_Intelligence_Platform/
│
├── config/
├── data/
│   ├── raw/
│   └── supporting/
│
├── outputs/
│   ├── validation_failures.csv
│   ├── load_audit.csv
│   ├── capital_allocation.csv
│   ├── screener_output.xlsx
│   ├── valuation_summary.xlsx
│   └── valuation_flags.csv
│
├── reports/
│   └── radar_charts/
│
├── src/
│   ├── analytics/
│   │   ├── ratio_engine.py
│   │   ├── peer.py
│   │   └── valuation.py
│   ├── dashboard/
│   │   ├── app.py
│   │   ├── pages/
│   │   └── utils/
│   ├── etl/
│   └── screener/
│
├── tests/
├── requirements.txt
└── README.md

---

## Implemented Modules

### Sprint 1 — Data Foundation

- Excel data ingestion
- Data normalization
- SQLite schema and loading
- 16 Data Quality rules
- Validation reports
- Load audit generation

### Sprint 2 — Financial Analytics

- Profitability ratios: ROE, ROCE, ROA, NPM, OPM
- Leverage and efficiency ratios
- Revenue, PAT and EPS CAGR
- Free Cash Flow and CapEx analysis
- Capital allocation classification
- Composite Quality Score

### Sprint 3 — Screener & Peer Comparison

#### Financial Screener

- 6 investment presets:
  - Quality
  - Value
  - Growth
  - Dividend
  - Debt-Free
  - Turnaround
- Multi-metric filtering
- Sector-aware screening
- Composite score integration
- CSV/Excel reporting

#### Peer Comparison

- Peer group mapping
- Percentile ranking
- Financial metric benchmarking
- Radar chart comparison

### Sprint 4 — Dashboard & Valuation

#### Interactive Dashboard

The Streamlit dashboard contains 8 screens:

1. **Home** — Nifty 100 overview and key KPIs
2. **Company Profile** — company-level financial analysis and trends
3. **Screener** — configurable financial screening and CSV export
4. **Peer Comparison** — peer benchmarking and radar charts
5. **Trend Analysis** — historical multi-metric trends
6. **Sector Analysis** — sector and sub-sector analytics
7. **Capital Allocation** — company capital allocation patterns
8. **Annual Reports** — available annual report links

#### Valuation Module

Implemented in:

src/analytics/valuation.py

Calculates:

- FCF Yield
- Sector median P/E
- P/E valuation comparison
- Caution / Discount / Fair classification

Valuation outputs:

- outputs/valuation_summary.xlsx
- outputs/valuation_flags.csv

The valuation module was validated for the complete 92-company universe.

---

## Dashboard

Run the Streamlit application with:

streamlit run src/dashboard/app.py

The dashboard runs locally at:

http://localhost:8501

---

## Validation

Sprint 4 dashboard verification confirmed:

- All 8 screens load successfully
- Company and year selections work
- Screener filters and presets work
- CSV export works
- Peer and radar analysis work
- Sector and capital allocation pages work
- Annual report availability is handled
- Missing financial data displays as N/A
- Missing pros/cons are handled gracefully
- Charts remain within the dashboard layout
- Valuation module produces results for all 92 companies

### Valuation Results

| Flag | Companies |
|---|---:|
| Fair | 48 |
| Discount | 30 |
| Caution | 14 |
| **Total** | **92** |

---

## Database

The SQLite warehouse contains structured tables including:

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

## Run the Project

### ETL

python -m src.etl.loader

### Validation

python -m src.etl.validator

### Financial Ratio Engine

python -m src.analytics.ratio_engine

### Screener

python -m src.screener.engine

### Peer Comparison

python -m src.analytics.peer

### Valuation

python src/analytics/valuation.py

### Dashboard

streamlit run src/dashboard/app.py

---

## Data

The original financial datasets are not included in this repository because they were provided as part of an internship project and are confidential.

Place supported datasets in:

data/raw/
data/supporting/

---

## Current Progress

| Module | Status |
|---|---|
| ETL & Data Foundation | ✅ Completed |
| Financial Ratio Engine | ✅ Completed |
| CAGR & Cash Flow Analytics | ✅ Completed |
| Composite Quality Scoring | ✅ Completed |
| Financial Screener | ✅ Completed |
| Peer Comparison | ✅ Completed |
| Radar Charts | ✅ Completed |
| Streamlit Dashboard | ✅ Completed |
| Valuation Module | ✅ Completed |
| Sprint 4 QA | ✅ Completed |
| Documentation | ✅ Completed |

---

## Author

**Nuha AjmalKhan Pathan**

Data Analyst Intern @ Bluestock Fintech