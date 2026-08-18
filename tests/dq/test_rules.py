# :::writing{variant="document" id="58321" title="tests/dq/test_rules.py"}
import pandas as pd

from src.etl.validator import (
    check_annual_report_url,
    check_balance_sheet,
    check_bse_ase_balance,
    check_company_year_pk,
    check_coverage,
    check_dividend_cap,
    check_eps_sign,
    check_fk_integrity,
    check_net_cash_flow,
    check_opm,
    check_pk_uniqueness,
    check_positive_sales,
    check_tax_percentage,
    check_year_format,
)


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def assert_failure(result, rule, severity):
    """Verify that a validation result contains the expected rule and severity."""
    assert not result.empty
    assert rule in result["rule"].values
    assert severity in result["severity"].values


# ------------------------------------------------------------------
# DQ-01 — Primary Key Uniqueness
# ------------------------------------------------------------------

def test_dq01_pk_uniqueness():
    """DQ-01 flags duplicate primary-key values."""
    df = pd.DataFrame(
        {
            "id": ["TCS", "INFY", "TCS"],
            "company_name": ["TCS", "Infosys", "TCS Duplicate"],
        }
    )

    result = check_pk_uniqueness(
        df,
        "companies",
        ["id"],
    )

    assert_failure(result, "DQ-01", "CRITICAL")
    assert len(result) == 2


# ------------------------------------------------------------------
# DQ-02 — Company-Year Uniqueness
# ------------------------------------------------------------------

def test_dq02_company_year_pk():
    """DQ-02 flags duplicate company-year combinations."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS", "TCS", "INFY"],
            "year": [2024, 2024, 2024],
            "sales": [1000, 1100, 900],
        }
    )

    result = check_company_year_pk(
        df,
        "profitandloss",
    )

    assert_failure(result, "DQ-02", "CRITICAL")
    assert len(result) == 2


# ------------------------------------------------------------------
# DQ-03 — Foreign Key Integrity
# ------------------------------------------------------------------

def test_dq03_fk_integrity():
    """DQ-03 flags company IDs missing from the companies table."""
    companies = pd.DataFrame(
        {
            "id": ["TCS", "INFY"],
            "company_name": ["TCS", "Infosys"],
        }
    )

    df = pd.DataFrame(
        {
            "company_id": ["TCS", "INVALID"],
            "year": [2024, 2024],
        }
    )

    result = check_fk_integrity(
        df,
        companies,
        "profitandloss",
    )

    assert_failure(result, "DQ-03", "CRITICAL")
    assert len(result) == 1
    assert result.iloc[0]["value"] == "INVALID"


# ------------------------------------------------------------------
# DQ-04 — Balance Sheet
# ------------------------------------------------------------------

def test_dq04_balance_sheet():
    """DQ-04 flags assets and liabilities differing by more than 1%."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": [2024],
            "total_assets": [1000.0],
            "total_liabilities": [900.0],
        }
    )

    result = check_balance_sheet(
        df,
        "balancesheet",
    )

    assert_failure(result, "DQ-04", "WARNING")
    assert len(result) == 1


# ------------------------------------------------------------------
# DQ-05 — Operating Profit Margin
# ------------------------------------------------------------------

def test_dq05_opm():
    """DQ-05 flags an incorrect operating profit margin."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": [2024],
            "operating_profit": [200.0],
            "sales": [1000.0],
            "opm_percentage": [10.0],
        }
    )

    result = check_opm(
        df,
        "profitandloss",
    )

    assert_failure(result, "DQ-05", "WARNING")
    assert len(result) == 1


# ------------------------------------------------------------------
# DQ-06 — Positive Sales
# ------------------------------------------------------------------

def test_dq06_positive_sales():
    """DQ-06 flags zero or negative sales."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": [2024],
            "sales": [0.0],
        }
    )

    result = check_positive_sales(
        df,
        "profitandloss",
    )

    assert_failure(result, "DQ-06", "WARNING")
    assert len(result) == 1


# ------------------------------------------------------------------
# DQ-07 — Year Format
# ------------------------------------------------------------------

def test_dq07_year_format():
    """DQ-07 flags invalid financial years."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": [1800],
        }
    )

    result = check_year_format(
        df,
        "profitandloss",
    )

    assert_failure(result, "DQ-07", "CRITICAL")
    assert len(result) == 1


# ------------------------------------------------------------------
# DQ-09 — Net Cash Flow
# ------------------------------------------------------------------

def test_dq09_net_cash_flow():
    """DQ-09 flags net cash flow inconsistent with its components."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": [2024],
            "operating_activity": [100.0],
            "investing_activity": [-50.0],
            "financing_activity": [20.0],
            "net_cash_flow": [200.0],
        }
    )

    result = check_net_cash_flow(
        df,
        "cashflow",
    )

    assert_failure(result, "DQ-09", "WARNING")
    assert len(result) == 1


# ------------------------------------------------------------------
# DQ-11 — Tax Percentage
# ------------------------------------------------------------------

def test_dq11_tax_percentage():
    """DQ-11 flags an incorrect tax percentage."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": [2024],
            "profit_before_tax": [100.0],
            "net_profit": [70.0],
            "tax_percentage": [10.0],
        }
    )

    result = check_tax_percentage(
        df,
        "profitandloss",
    )

    assert_failure(result, "DQ-11", "WARNING")
    assert len(result) == 1


# ------------------------------------------------------------------
# DQ-12 — Dividend Payout Cap
# ------------------------------------------------------------------

def test_dq12_dividend_cap():
    """DQ-12 flags dividend payout above the implemented threshold."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": [2024],
            "dividend_payout": [250.0],
        }
    )

    result = check_dividend_cap(
        df,
        "profitandloss",
    )

    assert_failure(result, "DQ-12", "WARNING")
    assert len(result) == 1


# ------------------------------------------------------------------
# DQ-13 — Annual Report URL
# ------------------------------------------------------------------

def test_dq13_annual_report_url():
    """DQ-13 flags an invalid annual-report URL."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "Year": [2024],
            "Annual_Report": ["not-a-valid-url"],
        }
    )

    result = check_annual_report_url(
        df,
        "documents",
    )

    assert_failure(result, "DQ-13", "WARNING")
    assert len(result) == 1


# ------------------------------------------------------------------
# DQ-14 — EPS Sign
# ------------------------------------------------------------------

def test_dq14_eps_sign():
    """DQ-14 flags EPS whose sign disagrees with net profit."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": [2024],
            "net_profit": [100.0],
            "eps": [-5.0],
        }
    )

    result = check_eps_sign(
        df,
        "profitandloss",
    )

    assert_failure(result, "DQ-14", "WARNING")
    assert len(result) == 1


# ------------------------------------------------------------------
# DQ-15 — Assets/Liabilities Equality Audit
# ------------------------------------------------------------------

def test_dq15_bse_ase_balance():
    """DQ-15 records the strict assets-liabilities audit result."""
    df = pd.DataFrame(
        {
            "company_id": ["TCS", "INFY"],
            "year": [2024, 2024],
            "total_assets": [1000.0, 2000.0],
            "total_liabilities": [1000.0, 1800.0],
        }
    )

    result = check_bse_ase_balance(
        df,
        "balancesheet",
    )

    assert not result.empty
    assert result.iloc[0]["rule"] == "DQ-15"
    assert result.iloc[0]["severity"] == "INFO"
    assert result.iloc[0]["rows_checked"] == 2
    assert result.iloc[0]["rows_flagged"] == 1


# ------------------------------------------------------------------
# DQ-16 — Financial History Coverage
# ------------------------------------------------------------------

def test_dq16_coverage():
    """DQ-16 flags companies with fewer than five years of history."""
    profitandloss = pd.DataFrame(
        {
            "company_id": ["TCS", "TCS", "TCS", "TCS"],
            "year": [2021, 2022, 2023, 2024],
        }
    )

    balancesheet = pd.DataFrame(
        {
            "company_id": ["TCS", "TCS", "TCS", "TCS"],
            "year": [2021, 2022, 2023, 2024],
        }
    )

    cashflow = pd.DataFrame(
        {
            "company_id": ["TCS", "TCS", "TCS", "TCS"],
            "year": [2021, 2022, 2023, 2024],
        }
    )

    datasets = {
        "profitandloss": profitandloss,
        "balancesheet": balancesheet,
        "cashflow": cashflow,
    }

    result = check_coverage(datasets)

    assert not result.empty
    assert set(result["rule"]) == {"DQ-16"}
    assert set(result["severity"]) == {"WARNING"}
    assert len(result) == 3
    assert set(result["table"]) == {
        "profitandloss",
        "balancesheet",
        "cashflow",
    }
