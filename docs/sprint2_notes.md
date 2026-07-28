# Sprint 2 Notes – Financial Ratio Engine

**Project:** N100 Financial Intelligence Platform  
**Sprint:** Sprint 2 – Financial Ratio Engine  
**Duration:** Day 08 – Day 14  
**Status:** Completed

---

# Sprint Goal

The objective of Sprint 2 was to design and implement the Financial Ratio Engine capable of computing financial KPIs for every company-year available in the dataset. The engine integrates Profit & Loss, Balance Sheet, Cash Flow, Market Cap, Company Master and Sector datasets into a unified analytics layer and stores the calculated metrics inside SQLite for downstream dashboards and screening.

---

# Files Implemented

The following modules were developed during Sprint 2:

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

Outputs generated:

```
outputs/
├── capital_allocation.csv
├── ratio_edge_cases.log
└── load_audit.csv
```

SQLite Tables

- financial_ratios
- company_growth_metrics

---

# Major Features Implemented

## Profitability Ratios

Implemented:

- Net Profit Margin
- Operating Profit Margin
- Return on Equity (ROE)
- Return on Capital Employed (ROCE)
- Return on Assets (ROA)

Safety checks included:

- Division by zero handling
- Negative equity handling
- Missing values handled using None

---

## Leverage Ratios

Implemented:

- Debt to Equity
- Interest Coverage Ratio
- Net Debt
- Asset Turnover

Additional flags:

- High Leverage Flag
- Interest Coverage Warning
- Debt Free Label

---

## Cash Flow Analytics

Implemented:

- Free Cash Flow
- CapEx Intensity
- FCF Conversion
- CFO Quality Score
- Capital Allocation Pattern Classification

Generated:

```
outputs/capital_allocation.csv
```

---

## CAGR Engine

Implemented:

- Revenue CAGR
- PAT CAGR
- EPS CAGR

Supported:

- 3-Year
- 5-Year
- 10-Year calculations

Handled edge cases:

- Zero base
- Negative values
- Insufficient history

---

## Composite Quality Score

A weighted quality score was implemented using:

- ROE
- ROCE
- Revenue CAGR
- Debt-to-Equity

The score is calculated on a 0–100 scale and stored in the financial_ratios table.

---

# Financial Ratios Generated

The following KPIs are stored for every company-year:

- Net Profit Margin
- Operating Profit Margin
- Return on Equity
- Return on Capital Employed
- Return on Assets
- Debt to Equity
- Interest Coverage
- Net Debt
- Asset Turnover
- Earnings Per Share
- Book Value Per Share
- Dividend Payout Ratio
- Free Cash Flow
- CapEx
- CapEx Intensity
- FCF Conversion
- Capital Allocation Pattern
- Revenue CAGR
- PAT CAGR
- EPS CAGR
- Composite Quality Score

---

# Validation Performed

The ratio engine performs validation before storing results.

Checks include:

- Duplicate company-year removal
- Merge diagnostics
- Row count verification
- Missing value detection
- SQLite insertion verification

Example merge summary:

```
Merged rows : 1164
Merged columns : 52
```

---

# Dataset Observations

During validation several observations were made regarding the source datasets.

### Balance Sheet

The Balance Sheet dataset contains duplicate records for certain company-year combinations.

Example:

```
BEL
2024
```

appears twice with different financial values.

Since the datasets were provided by the organization, these records were preserved rather than modified.

---

### Source ROE and ROCE

The Companies dataset contains pre-computed ROE and ROCE values.

These values differ significantly from ratios calculated directly from the Balance Sheet and Profit & Loss statements.

The implemented ratio engine computes ROE and ROCE using the financial statements rather than relying on the pre-computed company values.

---

### Book Value

Book Value Per Share is calculated using:

```
(Equity Capital + Reserves)
/ Equity Capital
```

The calculated values differ from the source Book Value column because the provided dataset appears to use a different methodology.

The project stores the calculated value for analytical consistency.

---

# Edge Cases Handled

The following situations are handled gracefully:

- Zero Sales
- Zero Assets
- Zero Equity
- Zero Interest Expense
- Debt Free Companies
- Negative Equity
- Missing Financial Years
- Missing Market Cap Records
- Duplicate Company-Year Records

All detected anomalies are written to:

```
outputs/ratio_edge_cases.log
```

---

# Outputs Generated

Successful execution generates:

```
financial_ratios
company_growth_metrics

outputs/
├── capital_allocation.csv
├── ratio_edge_cases.log
```

---

# Sprint Results

Processed Companies:

```
100
```

Company-Year Records:

```
1164
```

Financial Ratio Columns:

```
25+
```

Capital Allocation Records:

```
1164
```

Growth Records:

```
100
```

---

# Lessons Learned

- Financial ratios should always be computed from raw financial statements rather than relying solely on pre-computed values.
- Real-world datasets frequently contain inconsistencies, duplicate records and differing calculation methodologies.
- Validation and anomaly logging are essential components of financial analytics pipelines.
- Modular implementation simplifies testing and future enhancements.

---

# Sprint Completion Checklist

- [x] Profitability ratios implemented
- [x] Leverage ratios implemented
- [x] Cash Flow KPIs implemented
- [x] CAGR engine implemented
- [x] Composite Quality Score implemented
- [x] Financial ratios stored in SQLite
- [x] Company growth metrics generated
- [x] Capital allocation report generated
- [x] Edge case logging implemented
- [x] Sprint 2 deliverables completed

---

**Sprint Status:** Completed ✅