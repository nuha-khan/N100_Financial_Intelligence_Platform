# N100 Financial Intelligence Platform

A Python-based ETL and data validation platform for processing financial data of Nifty 100 companies. The project focuses on building a clean, validated, and structured data foundation for financial analytics using automated ETL pipelines and SQLite.

> 🚧 **Status:** Sprint 1 – Data Foundation (In Progress)

---

## Features

- Load data from 12 Excel datasets
- Data normalization for years and company tickers
- Automated validation using 16 Data Quality (DQ) rules
- Validation failure reporting
- Load audit generation
- SQLite database integration (In Progress)

---

## Tech Stack

- Python
- Pandas
- NumPy
- SQLite
- OpenPyXL

---

## Project Structure

```text
N100_Financial_Intelligence_Platform/
│
├── data/
├── db/
├── output/
├── src/
│   └── etl/
├── tests/
├── requirements.txt
└── README.md
```

---

## Implemented Modules

- Environment Setup
- Excel Loader
- Data Normalization
- Validator
- DQ-01 to DQ-16
- Validation Reports
- Load Audit

---

## Current Progress

| Module | Status |
|---------|--------|
| ETL Loader | ✅ Completed |
| Data Normalization | ✅ Completed |
| Data Validation | ✅ Completed |
| SQLite Schema | 🚧 In Progress |
| Database Loading | ⏳ Pending |
| Analytics Engine | ⏳ Pending |

---

## Output Files

- `validation_failures.csv` – Detailed validation failures
- `load_audit.csv` – ETL audit summary

---

## Data

This project processes financial data from multiple Excel sources.

> **Note:** The original datasets are not included in this repository as they were provided as part of an internship project and are confidential.

To run the project, place the required Excel files in:

```text
data/raw/
data/supporting/
```

The ETL pipeline will automatically discover and process all supported files.

## Run

```bash
python -m src.etl.loader
python -m src.etl.validator
```

---

## Author

**Nuha AjmalKhan Pathan**
Data Analyst Intern @ Bluestock Fintech