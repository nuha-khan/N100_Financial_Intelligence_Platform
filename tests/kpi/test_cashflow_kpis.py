import pandas as pd

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    capital_allocation_pattern,
)

def test_free_cash_flow():

    assert free_cash_flow(100, -40) == 60


def test_capex_intensity_asset_light():

    value, label = capex_intensity(-2, 100)

    assert value == 2.0
    assert label == "Asset Light"


def test_capex_intensity_moderate():

    value, label = capex_intensity(-5, 100)

    assert value == 5.0
    assert label == "Moderate"


def test_capex_intensity_capital_intensive():

    value, label = capex_intensity(-15, 100)

    assert value == 15.0
    assert label == "Capital Intensive"


def test_fcf_conversion_rate():

    assert fcf_conversion_rate(100, -20, 40) == 200.0

def test_cfo_quality_high():

    df = pd.DataFrame({

        "year":[2020,2021,2022,2023,2024],

        "operating_activity":[100,120,140,160,180],

        "net_profit":[80,90,100,110,120]

    })

    ratio,label = cfo_quality_score(df)

    assert label == "High Quality"


def test_cfo_quality_moderate():

    df = pd.DataFrame({

        "year":[2020,2021,2022,2023,2024],

        "operating_activity":[50,50,50,50,50],

        "net_profit":[80,80,80,80,80]

    })

    ratio,label = cfo_quality_score(df)

    assert label == "Moderate"


def test_cfo_quality_accrual_risk():

    df = pd.DataFrame({

        "year":[2020,2021,2022,2023,2024],

        "operating_activity":[10,10,10,10,10],

        "net_profit":[80,80,80,80,80]

    })

    ratio,label = cfo_quality_score(df)

    assert label == "Accrual Risk"


def test_cfo_quality_insufficient():

    df = pd.DataFrame({

        "year":[2023,2024],

        "operating_activity":[100,120],

        "net_profit":[80,90]

    })

    ratio,label = cfo_quality_score(df)

    assert ratio is None
    assert label == "INSUFFICIENT"

def test_reinvestor():

    assert capital_allocation_pattern(100, -50, -30) == "Reinvestor"


def test_shareholder_returns():

     assert capital_allocation_pattern(100, -50, -30) == "Reinvestor"


def test_distress():

    assert capital_allocation_pattern(-100, 40, 60) == "Distress Signal"


def test_growth_funded_by_debt():

    assert capital_allocation_pattern(
        -100,
        -50,
        70
    ) == "Growth Funded by Debt"


def test_cash_accumulator():

    assert capital_allocation_pattern(
        100,
        20,
        30
    ) == "Cash Accumulator"


def test_pre_revenue():

    assert capital_allocation_pattern(
        -100,
        -50,
        -20
    ) == "Pre-Revenue"


def test_mixed():

    assert capital_allocation_pattern(
        100,
        -50,
        20
    ) == "Mixed"