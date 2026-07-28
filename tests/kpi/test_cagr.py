import pytest
import pandas as pd

from src.analytics.cagr import (
    calculate_cagr,
    revenue_cagr,
    pat_cagr,
    eps_cagr,
)


# ==========================================================
# DAY 10 — CAGR ENGINE
# ==========================================================

def test_cagr_normal():

    cagr, flag = calculate_cagr(start_value=100, end_value=200, years=5)

    assert round(cagr, 2) == 14.87
    assert flag is None


def test_decline_to_loss():

    cagr, flag = calculate_cagr(start_value=100, end_value=-50, years=5)

    assert cagr is None
    assert flag == "DECLINE_TO_LOSS"


def test_turnaround():

    cagr, flag = calculate_cagr(start_value=-100, end_value=100, years=5)

    assert cagr is None
    assert flag == "TURNAROUND"


def test_both_negative():

    cagr, flag = calculate_cagr(start_value=-100, end_value=-50, years=5)

    assert cagr is None
    assert flag == "BOTH_NEGATIVE"


def test_zero_base():

    cagr, flag = calculate_cagr(start_value=0, end_value=100, years=5)

    assert cagr is None
    assert flag == "ZERO_BASE"


def test_insufficient_years():

    cagr, flag = calculate_cagr(start_value=100, end_value=200, years=0)

    assert cagr is None
    assert flag == "INSUFFICIENT"


def test_none_start():

    cagr, flag = calculate_cagr(start_value=None, end_value=100, years=5)

    assert cagr is None
    assert flag == "INSUFFICIENT"


def test_none_end():

    cagr, flag = calculate_cagr(start_value=100, end_value=None, years=5)

    assert cagr is None
    assert flag == "INSUFFICIENT"


def test_decimal_growth():

    cagr, flag = calculate_cagr(start_value=250, end_value=500, years=10)

    assert round(cagr, 2) == 7.18
    assert flag is None


def test_same_values():

    cagr, flag = calculate_cagr(start_value=100, end_value=100, years=5)

    assert cagr == 0.0
    assert flag is None

# ==========================================================
# CAGR WRAPPER TESTS
# ==========================================================

def sample_financial_data():
    return pd.DataFrame({
        "year": [2019, 2020, 2021, 2022, 2023, 2024],
        "sales": [100, 120, 140, 160, 180, 200],
        "net_profit": [20, 25, 30, 35, 40, 50],
        "eps": [2, 2.5, 3, 3.5, 4, 5],
    })


def test_revenue_cagr_wrapper():

    df = sample_financial_data()

    cagr, flag = revenue_cagr(df, 5)

    assert round(cagr, 2) == 14.87
    assert flag is None


def test_pat_cagr_wrapper():

    df = sample_financial_data()

    cagr, flag = pat_cagr(df, 5)

    assert round(cagr, 2) == 20.11
    assert flag is None


def test_eps_cagr_wrapper():

    df = sample_financial_data()

    cagr, flag = eps_cagr(df, 5)

    assert round(cagr, 2) == 20.11
    assert flag is None


def test_revenue_cagr_insufficient_history():

    df = pd.DataFrame({
        "year": [2023, 2024],
        "sales": [100, 120],
        "net_profit": [20, 25],
        "eps": [2, 2.5],
    })

    cagr, flag = revenue_cagr(df, 5)

    assert cagr is None
    assert flag == "INSUFFICIENT"