# N100 Financial Intelligence Platform

A Python-based financial intelligence platform for the **Nifty 100** that transforms raw financial data into structured analytics, investment insights, peer intelligence, valuation analysis, automated reports, and an interactive dashboard.

> **Status: Completed — Sprints 1–5**

---

## Overview

The platform processes financial data for **92 Nifty 100 companies** through an end-to-end analytics pipeline:

**Raw Data → ETL & Validation → SQLite Database → Financial Analytics → Intelligence & NLP → Reports → FastAPI → Streamlit Dashboard**

The platform combines fundamental financial analysis, cash-flow intelligence, peer benchmarking, screening, valuation, clustering, automated reporting, and NLP-generated investment pros and cons.

---

## Key Features

* Automated ETL pipeline for 12 financial datasets
* Data normalization and 16 Data Quality validation rules
* SQLite financial data warehouse
* 30+ financial KPIs and ratios
* Revenue, PAT and EPS CAGR analysis
* Free Cash Flow and CapEx analytics
* CFO quality and cash-flow intelligence
* Capital allocation classification
* Composite financial quality scoring
* Configurable financial screener with 6 investment presets
* Peer-group benchmarking and percentile analysis
* Radar chart analysis
* Company clustering and cluster profiling
* Valuation analytics including P/E and FCF Yield
* NLP-based investment pros and cons with confidence scores
* Automated company tearsheets
* Sector-level PDF reports
* Portfolio summary report
* FastAPI REST API
* Interactive Streamlit dashboard
* CSV and Excel exports
* Automated test suite
* SQLite query-performance indexes

---

## Tech Stack

### Core

* Python
* Pandas
* NumPy
* SQLite
* SQLAlchemy
* OpenPyXL
* PyYAML

### Analytics & Visualization

* Matplotlib
* Plotly
* Streamlit

### API & Reporting

* FastAPI
* Uvicorn
* ReportLab

### Testing & Development

* Pytest
* Git
* GitHub
* VS Code

---

# Project Architecture

```text
Raw Financial Data
       │
       ▼
┌─────────────────────┐
│     ETL Pipeline    │
│ Loader + Normalizer │
│     + Validator     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    SQLite Database  │
│     nifty100.db     │
└──────────┬──────────┘
           │
           ├──────────────► Financial Ratios
           ├──────────────► CAGR & Cash Flow
           ├──────────────► Capital Allocation
           ├──────────────► Peer Intelligence
           ├──────────────► Clustering
           ├──────────────► Valuation
           ├──────────────► Screener
           └──────────────► NLP Intelligence
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          FastAPI REST API          Automated Reports
                 │                         │
                 └────────────┬────────────┘
                              ▼
                    Streamlit Dashboard
```

---

# Project Structure

```text
N100_Financial_Intelligence_Platform/
│
├── config/
│   └── screener_config.yaml
│
├── data/
│   ├── raw/
│   └── supporting/
│
├── docs/
│
├── notebooks/
│
├── outputs/
│
├── reports/
│   ├── assets/
│   ├── radar_charts/
│   ├── tearsheets/
│   └── *.pdf
│
├── src/
│   ├── analytics/
│   │   ├── cagr.py
│   │   ├── capital_allocation.py
│   │   ├── cashflow_kpis.py
│   │   ├── clustering.py
│   │   ├── cluster_profiling.py
│   │   ├── insights.py
│   │   ├── peer.py
│   │   ├── radar.py
│   │   ├── ratios.py
│   │   ├── ratio_engine.py
│   │   └── valuation.py
│   │
│   ├── api/
│   │   ├── main.py
│   │   ├── database.py
│   │   └── routers/
│   │       ├── companies.py
│   │       ├── documents.py
│   │       ├── health.py
│   │       ├── market_cap.py
│   │       ├── peers.py
│   │       ├── portfolio.py
│   │       ├── screener.py
│   │       ├── sectors.py
│   │       └── valuation.py
│   │
│   ├── dashboard/
│   │   ├── app.py
│   │   ├── pages/
│   │   │   ├── 01_home.py
│   │   │   ├── 02_profile.py
│   │   │   ├── 03_screener.py
│   │   │   ├── 04_peers.py
│   │   │   ├── 05_trends.py
│   │   │   ├── 06_sectors.py
│   │   │   ├── 07_capital.py
│   │   │   └── 08_reports.py
│   │   └── utils/
│   │
│   ├── etl/
│   │   ├── loader.py
│   │   ├── normaliser.py
│   │   └── validator.py
│   │
│   ├── nlp/
│   │   ├── parser.py
│   │   └── pros_cons_generator.py
│   │
│   ├── reports/
│   │   ├── tearsheet.py
│   │   ├── batch_reports.py
│   │   └── portfolio_report.py
│   │
│   └── screener/
│       ├── engine.py
│       ├── scoring.py
│       └── export.py
│
├── tests/
│   ├── api/
│   ├── dq/
│   └── performance/
│
├── Makefile
├── requirements.txt
└── README.md
```

---

# Major Modules

## 1. ETL & Data Quality

The ETL layer loads and normalizes the financial datasets before storing them in SQLite.

Implemented:

* Excel ingestion
* Year normalization
* Company/ticker normalization
* Database creation and loading
* Primary-key validation
* Company-year uniqueness validation
* Foreign-key integrity checks
* Balance-sheet validation
* OPM validation
* Positive-sales validation
* Year-format validation
* Cash-flow validation
* Tax and dividend validation
* Annual-report URL validation
* EPS validation
* BSE/ASE balance validation
* Coverage validation

---

## 2. Financial Analytics

The analytics layer calculates fundamental financial metrics including:

* Net Profit Margin
* Operating Profit Margin
* ROE
* ROCE
* ROA
* Debt-to-Equity
* Interest Coverage
* Net Debt
* Asset Turnover
* EPS
* Book Value per Share
* Dividend Payout
* Revenue CAGR
* PAT CAGR
* EPS CAGR
* Free Cash Flow
* FCF Conversion
* CapEx Intensity
* CFO Quality
* Capital Allocation Pattern
* Composite Quality Score

---

## 3. Cash Flow Intelligence

Cash-flow analysis evaluates the quality and sustainability of company cash generation.

The module identifies:

* CFO quality
* Free cash flow
* FCF conversion
* CapEx intensity
* Capital allocation patterns
* Deleveraging behaviour
* Cash-flow distress signals
* FCF growth

---

## 4. Investment Screener

The screener supports configurable multi-metric filtering and six predefined investment strategies:

1. Quality
2. Value
3. Growth
4. Dividend
5. Debt-Free
6. Turnaround

Results can be exported for further analysis.

---

## 5. Peer Intelligence

The peer analytics module provides:

* Peer-group classification
* Financial benchmarking
* Percentile rankings
* Company-vs-peer comparison
* Radar chart visualization
* Peer-based financial positioning

---

## 6. Clustering & Advanced Analytics

Companies are grouped using financial characteristics to identify similar business/financial profiles.

Implemented:

* Feature preparation
* Missing-value handling
* Sector-median imputation
* Cluster analysis
* Elbow analysis
* Cluster naming
* Cluster profiling
* Correlation analysis
* Outlier reporting
* Portfolio statistics

---

## 7. Valuation

The valuation module evaluates companies using fundamental valuation indicators including:

* P/E ratio
* Five-year median P/E
* Sector median P/E
* FCF Yield
* Valuation flags

Companies are categorized into valuation conditions such as:

* Fair
* Discount
* Caution

---

# NLP Investment Intelligence

The NLP module parses analytical data and generates rule-based investment insights.

For each company, the system evaluates financial conditions and generates:

* Investment Pros
* Investment Cons
* Confidence scores
* Coverage information

The system uses predefined financial rules rather than free-form text generation, allowing the generated signals to remain traceable to underlying financial metrics.

---

# Automated Reports

The reporting layer generates:

### Company Tearsheets

Individual financial tearsheets containing:

* Company overview
* Financial KPIs
* Revenue and profit trends
* ROE/ROCE analysis
* Balance-sheet analysis
* Cash-flow analysis
* Capital allocation
* Investment pros and cons
* Financial visualizations

### Sector Reports

Sector-level reports summarize company and sector financial characteristics.

### Portfolio Report

A consolidated portfolio-level PDF provides a high-level view of the Nifty 100 financial universe.

---

# FastAPI

The platform exposes its analytical data through a REST API.

Available API modules include:

* Companies
* Documents
* Health
* Market Capitalization
* Peers
* Portfolio
* Screener
* Sectors
* Valuation

### API Base URL

```text
http://127.0.0.1:8000
```

### Health Check

```text
GET /api/v1/health
```

The health endpoint reports application status, database row counts, uptime, and API version.

Interactive API documentation is available through FastAPI's standard documentation interface when the server is running.

---

# Streamlit Dashboard

The platform contains **8 interactive dashboard screens**:

1. **Home** — Nifty 100 overview and key KPIs
2. **Company Profile** — company-level financial analysis
3. **Screener** — configurable investment screening
4. **Peer Comparison** — peer benchmarking and radar analysis
5. **Trend Analysis** — historical financial trends
6. **Sector Analysis** — sector-level analytics
7. **Capital Allocation** — market and capital allocation analysis
8. **Reports & Insights** — executive insights, radar charts and generated reports

### Run Dashboard

```bash
streamlit run src/dashboard/app.py
```

Dashboard:

```text
http://localhost:8501
```

---

# Database

The project uses SQLite as its analytical data warehouse.

Key tables include:

```text
companies
profitandloss
balancesheet
cashflow
financial_ratios
company_growth_metrics
market_cap
stock_prices
sectors
peer_groups
peer_percentiles
documents
analysis
prosandcons
```

Performance indexes were added for frequently queried company/year combinations, including:

```text
idx_profitandloss_company_year
idx_balancesheet_company_year
idx_cashflow_company_year
idx_financial_ratios_company_year
idx_documents_company_year
idx_market_cap_company_year
idx_peer_percentiles_company_year
idx_company_growth_metrics_company
```

Performance observations are documented separately in:

```text
perf_notes.md
```

---

# Testing

The project includes automated tests covering:

* API endpoints
* Data-quality validation
* Database behaviour
* Performance-related checks

Run the complete test suite with:

```bash
pytest -v tests/
```

---

# Makefile Commands

Common project operations are available through the Makefile:

```bash
make load
make validate
make ratios
make test
make report
make dashboard
make api
make clean
```

---

# Running the Project

### 1. Activate virtual environment

Windows:

```bash
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Load data

```bash
python -m src.etl.loader
```

### 4. Validate data

```bash
python -m src.etl.validator
```

### 5. Generate financial ratios

```bash
python -m src.analytics.ratio_engine
```

### 6. Run analytics as required

Examples:

```bash
python -m src.screener.engine
python -m src.analytics.peer
python -m src.analytics.clustering
python -m src.analytics.cluster_profiling
```

### 7. Start API

```bash
uvicorn src.api.main:app --reload
```

### 8. Start dashboard

```bash
streamlit run src/dashboard/app.py
```

---

# Data Availability

The original financial datasets are not included in this repository because they were provided as part of the internship project and are confidential.

Supported input data should be placed under:

```text
data/raw/
data/supporting/
```

---

# Project Completion

| Component                       | Status      |
| ------------------------------- | ----------- |
| ETL & Data Foundation           | ✅ Completed |
| Data Quality Validation         | ✅ Completed |
| Financial Ratio Engine          | ✅ Completed |
| CAGR & Cash Flow Analytics      | ✅ Completed |
| Capital Allocation Intelligence | ✅ Completed |
| Financial Screener              | ✅ Completed |
| Peer Intelligence               | ✅ Completed |
| Radar Analysis                  | ✅ Completed |
| Clustering & Advanced Analytics | ✅ Completed |
| Valuation Module                | ✅ Completed |
| NLP Pros & Cons                 | ✅ Completed |
| Company Tearsheets              | ✅ Completed |
| Sector Reports                  | ✅ Completed |
| Portfolio Report                | ✅ Completed |
| FastAPI Backend                 | ✅ Completed |
| Streamlit Dashboard             | ✅ Completed |
| Automated Testing               | ✅ Completed |
| Database Performance Indexing   | ✅ Completed |
| Documentation                   | ✅ Completed |

---

## Author

**Nuha AjmalKhan Pathan**

Data Analyst Intern @ Bluestock Fintech
