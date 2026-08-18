# N100 Financial Intelligence Platform — Analytics Documentation

## Overview

The analytics layer transforms structured financial data from the SQLite warehouse into financial metrics, investment signals, peer intelligence, valuation indicators, and automated reports.

The analytics pipeline is designed around company-level and sector-level financial analysis for the **92-company Nifty 100 universe**.

---

## 1. Financial Ratio Engine

Module:

```text
src/analytics/ratio_engine.py
```

The ratio engine combines financial statement data and calculates fundamental performance indicators.

### Profitability

* Net Profit Margin
* Operating Profit Margin
* Return on Equity
* Return on Capital Employed
* Return on Assets

### Leverage

* Debt-to-Equity
* Interest Coverage
* Net Debt
* Total Debt

### Efficiency

* Asset Turnover

### Shareholder Metrics

* Earnings Per Share
* Book Value Per Share
* Dividend Payout Ratio

### Quality

A composite financial quality score is calculated from selected profitability, leverage, and efficiency indicators.

---

## 2. Growth Analytics

Module:

```text
src/analytics/cagr.py
```

The platform calculates compounded growth rates for:

* Revenue
* Profit After Tax
* Earnings Per Share

Growth metrics are used throughout the screener, company analysis, valuation, and reporting modules.

---

## 3. Cash Flow Intelligence

Module:

```text
src/analytics/cashflow_kpis.py
```

Cash-flow analytics evaluates the quality and sustainability of company cash generation.

### Key Metrics

* Cash Flow from Operations
* Free Cash Flow
* FCF Conversion
* FCF CAGR
* CapEx
* CapEx Intensity
* CFO Quality Score
* CFO Quality Label

### Intelligence Signals

The module also identifies:

* Cash-flow distress signals
* Deleveraging behaviour
* Capital allocation patterns
* Persistent positive or negative cash-flow trends

---

## 4. Capital Allocation

Module:

```text
src/analytics/capital_allocation.py
```

Companies are classified according to their capital allocation behaviour using financial and cash-flow indicators.

The analysis considers:

* Operating cash generation
* Capital expenditure
* Debt movement
* Investments
* Shareholder distributions

The resulting classifications are used by the dashboard and company reports.

---

## 5. Investment Screener

Modules:

```text
src/screener/
```

The screener applies configurable financial conditions to identify companies matching different investment strategies.

### Presets

1. Quality
2. Value
3. Growth
4. Dividend
5. Debt-Free
6. Turnaround

The screener supports:

* Multiple financial filters
* Threshold-based conditions
* Sector-aware analysis
* Composite scoring
* Exportable results

---

## 6. Peer Intelligence

Modules:

```text
src/analytics/peer.py
src/analytics/peer_report.py
```

Peer analysis groups comparable companies and evaluates their relative financial performance.

### Outputs

* Peer groups
* Metric percentiles
* Company-vs-peer comparison
* Peer benchmark tables
* Radar chart inputs

Percentile rankings provide relative positioning of a company within its peer group.

---

## 7. Radar Analysis

Module:

```text
src/analytics/radar.py
```

Radar analysis provides a visual comparison between a selected company and its peer benchmark.

Metrics are normalized before visualization so that indicators with different scales can be compared within a single chart.

---

## 8. Sector Analytics

Sector analysis aggregates company-level financial information to identify differences in:

* Financial quality
* Profitability
* Market capitalization
* Growth
* Capital allocation

Sector-level outputs are displayed through the Streamlit dashboard and used in analytical reports.

---

## 9. Valuation Analytics

Module:

```text
src/analytics/valuation.py
```

The valuation module evaluates companies using fundamental market and financial metrics.

### Valuation Metrics

* Current P/E
* Five-year median P/E
* Sector median P/E
* FCF Yield
* Enterprise value
* Market capitalization

### Valuation Flags

Companies are classified using valuation comparisons such as:

* Fair
* Discount
* Caution

The results are exported to analytical output files and exposed through the API.

---

## 10. Clustering & Advanced Analytics

Modules:

```text
src/analytics/clustering.py
src/analytics/cluster_profiling.py
```

The clustering workflow groups companies according to selected financial characteristics.

### Processing Steps

1. Load analytical features
2. Prepare the latest company-level dataset
3. Handle missing values
4. Apply sector-median imputation where required
5. Generate clustering features
6. Evaluate cluster count using elbow analysis
7. Assign cluster labels
8. Profile cluster characteristics
9. Identify outliers
10. Generate portfolio statistics

Additional outputs include:

* Cluster profiles
* Correlation heatmap
* Outlier report
* Portfolio-level statistics

---

## 11. NLP Investment Intelligence

Modules:

```text
src/nlp/parser.py
src/nlp/pros_cons_generator.py
```

The NLP component converts structured financial metrics into interpretable investment signals.

### Processing

1. Parse analytical inputs
2. Extract financial growth and quality metrics
3. Evaluate predefined financial rules
4. Generate positive investment signals
5. Generate negative investment signals
6. Calculate confidence scores
7. Produce company-level pros and cons
8. Generate coverage reports

The implementation uses deterministic financial rules so that generated insights remain explainable and traceable to the underlying metrics.

---

## 12. Automated Reporting

Modules:

```text
src/reports/tearsheet.py
src/reports/batch_reports.py
src/reports/portfolio_report.py
```

### Company Tearsheets

Company-level PDF reports include:

* Company overview
* Financial KPIs
* Growth analysis
* Profitability indicators
* Balance-sheet information
* Cash-flow intelligence
* Capital allocation
* Investment pros and cons
* Financial charts

### Sector Reports

Sector reports aggregate company-level metrics into sector-level summaries.

### Portfolio Report

The portfolio report provides a consolidated view of the financial universe.

---

## 13. Streamlit Dashboard

The dashboard contains eight analytical screens:

| Screen             | Purpose                        |
| ------------------ | ------------------------------ |
| Home               | Nifty 100 overview             |
| Company Profile    | Detailed company analysis      |
| Screener           | Financial screening            |
| Peer Comparison    | Peer benchmarking              |
| Trend Analysis     | Historical trends              |
| Sector Analysis    | Sector-level intelligence      |
| Capital Allocation | Capital deployment analysis    |
| Reports & Insights | Reports and analytical outputs |

The dashboard reads from the SQLite analytical database and presents the processed results interactively.

---

## 14. FastAPI Integration

The analytics layer is exposed through REST endpoints implemented under:

```text
src/api/
```

The API provides access to:

* Companies
* Financial statements
* Ratios
* Cash flow
* Peers
* Sectors
* Screener
* Valuation
* Market capitalization
* Documents
* Portfolio analytics

This separates the analytical backend from the presentation layer and allows the processed data to be consumed programmatically.

---

## 15. Data Flow

The overall analytical flow is:

```text
Raw Excel Data
      ↓
Normalization
      ↓
Data Quality Validation
      ↓
SQLite Warehouse
      ↓
Financial Ratio Engine
      ↓
Growth & Cash Flow Analytics
      ↓
Peer / Sector / Valuation Analysis
      ↓
Clustering & NLP Intelligence
      ↓
Reports + FastAPI + Streamlit
```

---

## 16. Output Artifacts

Major analytical outputs include:

```text
outputs/
├── validation_failures.csv
├── load_audit.csv
├── capital_allocation.csv
├── valuation_flags.csv
├── valuation_summary.xlsx
├── screener_output.xlsx
├── pros_cons_generated.csv
└── pros_cons_coverage.csv
```

Additional report outputs are stored under:

```text
reports/
├── tearsheets/
├── radar_charts/
├── assets/
└── *.pdf
```

---

## 17. Design Principles

The analytics implementation follows these principles:

* Reproducible calculations
* Explicit financial rules
* Company-level traceability
* Graceful handling of missing data
* Separation of ETL, analytics, API, dashboard, and reporting layers
* Reusable analytical functions
* Exportable analytical outputs
* Validation before downstream analysis

This architecture allows additional financial metrics, screening rules, analytical modules, and API endpoints to be added without restructuring the complete platform.
