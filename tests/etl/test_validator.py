"""
Unit Tests for validator.py

Tests:
DQ-01
DQ-02
DQ-03
DQ-04
"""

import pandas as pd
import pytest

from src.etl.validator import *

############################################################
# Fixtures
############################################################

@pytest.fixture
def companies():
    return pd.DataFrame({"id": ["ABB", "TCS", "INFY"]})


@pytest.fixture
def profit_loss():
    return pd.DataFrame({
        "company_id": ["ABB"],
        "year": [2024],
        "sales": [100],
        "operating_profit": [25],
        "opm_percentage": [25],
        "profit_before_tax": [40],
        "net_profit": [30],
        "tax_percentage": [25],
        "dividend_payout": [40],
        "eps": [3]
    })


@pytest.fixture
def balance_sheet():
    return pd.DataFrame({
        "company_id": ["ABB"],
        "year": [2024],
        "total_assets": [100],
        "total_liabilities": [100]
    })


@pytest.fixture
def cashflow():
    return pd.DataFrame({
        "company_id": ["ABB"],
        "year": [2024],
        "operating_activity": [100],
        "investing_activity": [-20],
        "financing_activity": [-30],
        "net_cash_flow": [50]
    })


@pytest.fixture
def documents():
    return pd.DataFrame({
        "company_id": ["ABB"],
        "Year": [2024],
        "Annual_Report": ["https://company.com/report.pdf"]
    })

############################################################
# DQ-01
############################################################

def test_dq01_pass(companies):
    failures = check_pk_uniqueness(companies,"companies",["id"])

    assert failures.empty


def test_dq01_fail(companies):
    companies.loc[2, "id"] = "ABB"
    failures = check_pk_uniqueness(companies,"companies",["id"])

    assert len(failures) == 2
    assert failures.iloc[0]["rule"] == "DQ-01"

############################################################
# DQ-02
############################################################

def test_dq02_pass(profit_loss):
    failures = check_company_year_pk(profit_loss,"profitandloss")

    assert failures.empty


def test_dq02_fail(profit_loss):
    duplicate = profit_loss.copy()
    df = pd.concat([profit_loss, duplicate], ignore_index=True)

    failures = check_company_year_pk(df,"profitandloss")

    assert len(failures) == 2
    assert failures.iloc[0]["rule"] == "DQ-02"

############################################################
# DQ-03
############################################################

def test_dq03_pass(companies, profit_loss):
    failures = check_fk_integrity(profit_loss,companies,"profitandloss")

    assert failures.empty


def test_dq03_fail(companies, profit_loss):
    profit_loss.loc[0, "company_id"] = "XYZ"

    failures = check_fk_integrity(profit_loss,companies,"profitandloss")

    assert len(failures) == 1
    assert failures.iloc[0]["rule"] == "DQ-03"

############################################################
# DQ-04
############################################################

def test_dq04_pass(balance_sheet):
    failures = check_balance_sheet(balance_sheet,"balancesheet")

    assert failures.empty


def test_dq04_fail(balance_sheet):
    balance_sheet.loc[0, "total_liabilities"] = 80

    failures = check_balance_sheet(balance_sheet,"balancesheet")

    assert len(failures) == 1
    assert failures.iloc[0]["rule"] == "DQ-04"

############################################################
# DQ-05
############################################################

def test_dq05_pass(profit_loss):
    failures = check_opm(profit_loss,"profitandloss")

    assert failures.empty


def test_dq05_fail(profit_loss):
    profit_loss.loc[0, "opm_percentage"] = 10

    failures = check_opm(profit_loss,"profitandloss")

    assert len(failures) == 1
    assert failures.iloc[0]["rule"] == "DQ-05"


############################################################
# DQ-06
############################################################

def test_dq06_pass(profit_loss):
    failures = check_positive_sales(profit_loss,"profitandloss")

    assert failures.empty


def test_dq06_fail(profit_loss):
    profit_loss.loc[0, "sales"] = -50

    failures = check_positive_sales(profit_loss,"profitandloss")

    assert len(failures) == 1
    assert failures.iloc[0]["rule"] == "DQ-06"


############################################################
# DQ-07
############################################################

def test_dq07_year_pass(profit_loss):
    failures = check_year_format(profit_loss,"profitandloss")

    assert failures.empty


def test_dq07_year_fail(profit_loss):
    profit_loss.loc[0, "year"] = None

    failures = check_year_format(profit_loss,"profitandloss")

    assert len(failures) == 1
    assert failures.iloc[0]["rule"] == "DQ-07"


def test_dq07_documents_pass(documents):
    failures = check_year_format(documents,"documents")

    assert failures.empty


def test_dq07_documents_fail(documents):
    documents.loc[0, "Year"] = None

    failures = check_year_format(documents,"documents")

    assert len(failures) == 1


def test_dq07_stock_prices_pass():
    df = pd.DataFrame({
        "company_id": ["ABB"],
        "date": ["2024-03-31"]
    })

    failures = check_year_format(df,"stock_prices")

    assert failures.empty


def test_dq07_stock_prices_fail():
    df = pd.DataFrame({
        "company_id": ["ABB"],
        "date": ["Invalid Date"]
    })

    failures = check_year_format(df,"stock_prices")

    assert len(failures) == 1

############################################################
# DQ-09
############################################################

def test_dq09_pass(cashflow):
    failures = check_net_cash_flow(cashflow,"cashflow")

    assert failures.empty


def test_dq09_fail(cashflow):
    cashflow.loc[0, "net_cash_flow"] = 999

    failures = check_net_cash_flow(cashflow,"cashflow")

    assert len(failures) == 1
    assert failures.iloc[0]["rule"] == "DQ-09"

############################################################
# DQ-11
############################################################

def test_dq11_pass(profit_loss):
    failures = check_tax_percentage(profit_loss,"profitandloss")

    assert failures.empty


def test_dq11_fail(profit_loss):
    profit_loss.loc[0, "tax_percentage"] = 50

    failures = check_tax_percentage(profit_loss,"profitandloss")

    assert len(failures) == 1
    assert failures.iloc[0]["rule"] == "DQ-11"


############################################################
# DQ-12
############################################################

def test_dq12_pass(profit_loss):
    failures = check_dividend_cap(profit_loss,"profitandloss")

    assert failures.empty


def test_dq12_fail(profit_loss):
    profit_loss.loc[0, "dividend_payout"] = 250

    failures = check_dividend_cap(profit_loss,"profitandloss")

    assert len(failures) == 1
    assert failures.iloc[0]["rule"] == "DQ-12"


############################################################
# DQ-13
############################################################

def test_dq13_pass(documents):
    failures = check_annual_report_url(documents,"documents")

    assert failures.empty


def test_dq13_fail_null(documents):
    documents.loc[0, "Annual_Report"] = "Null"

    failures = check_annual_report_url(documents,"documents")

    assert len(failures) == 1


def test_dq13_fail_invalid_url(documents):
    documents.loc[0, "Annual_Report"] = "company.com/report.pdf"

    failures = check_annual_report_url(documents,"documents")

    assert len(failures) == 1


############################################################
# DQ-14
############################################################

def test_dq14_pass(profit_loss):
    failures = check_eps_sign(profit_loss,"profitandloss")

    assert failures.empty


def test_dq14_fail(profit_loss):
    profit_loss.loc[0, "eps"] = -3

    failures = check_eps_sign(profit_loss,"profitandloss")

    assert len(failures) == 1
    assert failures.iloc[0]["rule"] == "DQ-14"


############################################################
# DQ-15
############################################################

def test_dq15_pass(balance_sheet):
    audit = check_bse_ase_balance(balance_sheet,"balancesheet")

    assert audit.iloc[0]["rows_flagged"] == 0


def test_dq15_fail(balance_sheet):
    balance_sheet.loc[0, "total_liabilities"] = 95

    audit = check_bse_ase_balance(balance_sheet,"balancesheet")

    assert audit.iloc[0]["rows_flagged"] == 1


############################################################
# DQ-16
############################################################

def test_dq16_pass():
    datasets = {
        "profitandloss": pd.DataFrame({
            "company_id": ["ABB"] * 5,
            "year": [2020, 2021, 2022, 2023, 2024]
        }),

        "balancesheet": pd.DataFrame({
            "company_id": ["ABB"] * 5,
            "year": [2020, 2021, 2022, 2023, 2024]
        }),

        "cashflow": pd.DataFrame({
            "company_id": ["ABB"] * 5,
            "year": [2020, 2021, 2022, 2023, 2024]
        }),
    }

    failures = check_coverage(datasets)

    assert failures.empty


def test_dq16_fail():
    datasets = {
        "profitandloss": pd.DataFrame({
            "company_id": ["ABB"] * 3,
            "year": [2022, 2023, 2024]
        }),

        "balancesheet": pd.DataFrame({
            "company_id": ["ABB"] * 3,
            "year": [2022, 2023, 2024]
        }),

        "cashflow": pd.DataFrame({
            "company_id": ["ABB"] * 3,
            "year": [2022, 2023, 2024]
        }),
    }

    failures = check_coverage(datasets)

    assert len(failures) == 3
    assert (failures["rule"] == "DQ-16").all()