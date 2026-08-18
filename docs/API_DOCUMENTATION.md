# N100 Financial Intelligence Platform — API Documentation

## Overview

The N100 Financial Intelligence Platform exposes financial analytics through a REST API built with **FastAPI**.

The API provides access to company financials, ratios, peers, sectors, valuation data, screening, portfolio information, market capitalization, and annual reports.

## Running the API

Start the development server:

```bash
uvicorn src.api.main:app --reload
```

Default local address:

```text
http://127.0.0.1:8000
```

FastAPI automatically provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## Health Check

```http
GET /api/v1/health
```

Returns application status, database row counts, uptime, and API version.

Example:

```json
{
  "status": "ok",
  "db_row_counts": {
    "companies": 92,
    "financial_ratios": 1164,
    "documents": 1585
  },
  "version": "1.0.0"
}
```

## Company Endpoints

### List Companies

```http
GET /api/v1/companies/
```

Returns the available Nifty 100 companies.

### Company Details

```http
GET /api/v1/companies/{company_id}
```

Returns company-level information.

### Profit & Loss

```http
GET /api/v1/companies/{company_id}/pl
```

Returns historical profit and loss information.

### Balance Sheet

```http
GET /api/v1/companies/{company_id}/bs
```

Returns historical balance-sheet information.

### Cash Flow

```http
GET /api/v1/companies/{company_id}/cashflow
```

Returns historical cash-flow information.

### Financial Ratios

```http
GET /api/v1/companies/{company_id}/ratios
```

Returns calculated financial ratios and analytical KPIs.

### Company Tearsheet

```http
GET /api/v1/companies/{company_id}/tearsheet
```

Returns company-level tearsheet information.

### Peer Comparison

```http
GET /api/v1/companies/{company_id}/peers/compare
```

Compares the company against its peer group.

## Document Endpoints

```http
GET /api/v1/documents/{company_id}
```

Returns available annual reports for a company.

```http
GET /api/v1/documents/{company_id}/latest
```

Returns the latest available annual report.

```http
GET /api/v1/documents/{company_id}/{year}
```

Returns the annual report record for a specific year.

## Market Capitalization

```http
GET /api/v1/market-cap/{ticker}
```

Returns market capitalization and valuation-related market data.

## Peer Intelligence

```http
GET /api/v1/peers/
GET /api/v1/peers/group/{group_name}
GET /api/v1/peers/{company_id}
GET /api/v1/peers/{company_id}/percentiles
GET /api/v1/peers/{company_id}/compare
```

These endpoints provide peer groups, percentile rankings, and company-vs-peer comparisons.

## Portfolio

```http
GET /api/v1/portfolio/stats
GET /api/v1/portfolio/{company_id}
GET /api/v1/portfolio/{company_id}/prices
GET /api/v1/portfolio/{company_id}/financials
```

Provides portfolio-level statistics, price history, and financial history.

## Screener

```http
GET /api/v1/screener/
```

Runs configurable financial screening using available financial metrics.

```http
GET /api/v1/screener/templates
```

Returns available predefined screening templates.

## Sector Analytics

```http
GET /api/v1/sectors/
GET /api/v1/sectors/{sector}/companies
GET /api/v1/sectors/{company_id}
GET /api/v1/sectors/summary/all
```

Provides sector-level information, company membership, and sector summaries.

## Valuation

```http
GET /api/v1/valuation/{company_id}
GET /api/v1/valuation/{company_id}/history
GET /api/v1/valuation/{company_id}/summary
```

Provides company valuation metrics, historical valuation information, and summary flags.

## Error Handling

The API uses standard HTTP status codes.

Common responses include:

* `200` — Successful request
* `404` — Requested company/resource not found
* `422` — Invalid request parameters
* `500` — Internal server error

## Database

The API reads analytical data from:

```text
data/nifty100.db
```

The database contains financial statements, ratios, market data, peer intelligence, company growth metrics, documents, and other analytical outputs.

## Interactive API Testing

The recommended method for testing endpoints during development is the FastAPI Swagger interface:

```text
http://127.0.0.1:8000/docs
```

Endpoints can be executed directly from the browser and their JSON responses inspected.

## Validation

The API health endpoint was verified successfully during final project testing.

The Streamlit dashboard was also verified to load successfully from:

```text
http://127.0.0.1:8501
```

Both services operate against the same SQLite analytical database.
