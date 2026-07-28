import pytest

from src.analytics.ratios import *

# ==========================================================
# DAY 08 — PROFITABILITY RATIOS
# ==========================================================

def test_net_profit_margin_normal():

    assert net_profit_margin(20, 100) == 20.0

def test_net_profit_margin_zero_sales():

    assert net_profit_margin(20, 0) is None

def test_operating_profit_margin_normal():

    assert operating_profit_margin(25, 100) == 25.0

def test_return_on_equity_normal():

    assert return_on_equity(net_profit=25, equity_capital=50, reserves=50) == 25.0

def test_return_on_equity_negative_equity():

    assert return_on_equity(net_profit=20, equity_capital=-100, reserves=50) is None

def test_return_on_capital_employed_normal():

    assert return_on_capital_employed(operating_profit=30, equity_capital=50, reserves=50, borrowings=100) == 15.0

def test_return_on_assets_zero_assets():

    assert return_on_assets(net_profit=50, total_assets=0) is None

def test_opm_matches_source_pass():

    assert opm_matches_source(operating_profit=25, sales=100, source_opm=25) is True

def test_opm_matches_source_fail():

    assert opm_matches_source(operating_profit=25, sales=100, source_opm=20) is False

# ==========================================================
# DAY 09 — LEVERAGE & EFFICIENCY RATIOS
# ==========================================================

def test_debt_to_equity_normal():

    assert debt_to_equity(borrowings=200, equity_capital=100, reserves=100) == 1.0

def test_debt_to_equity_debt_free():

    assert debt_to_equity(borrowings=0, equity_capital=100, reserves=200) == 0

def test_debt_to_equity_negative_equity():

    assert debt_to_equity(borrowings=100, equity_capital=-50, reserves=0) is None

def test_high_leverage_flag():

    assert high_leverage_flag(6.5, "Industrials") is True

    assert high_leverage_flag(6.5, "Financials") is False

def test_interest_coverage_ratio():

    assert interest_coverage_ratio(operating_profit=100, other_income=20, interest=10) == 12.0

def test_interest_coverage_interest_zero():

    assert interest_coverage_ratio(operating_profit=100, other_income=20, interest=0) is None

def test_icr_label():

    assert icr_label(None) == "Debt Free"

    assert icr_label(4.5) == ""

def test_icr_warning_flag():

    assert icr_warning_flag(1.2) is True

    assert icr_warning_flag(2.8) is False

    assert icr_warning_flag(None) is False

def test_net_debt():

    assert net_debt(borrowings=500, investments=120) == 380

def test_asset_turnover():

    assert asset_turnover(sales=1000,total_assets=500) == 2.0

    assert asset_turnover(sales=1000, total_assets=0) is None