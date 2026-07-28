import math

def net_profit_margin(net_profit, sales):
    """
    Net Profit Margin (%)
    Formula:
        (Net Profit / Sales) * 100
    Returns
    -------
    float | None
    """

    if sales in (0, None):
        return None

    return round((net_profit / sales) * 100, 2)


def operating_profit_margin(operating_profit, sales):
    """
    Operating Profit Margin (%)
    Formula:
        (Operating Profit / Sales) * 100
    """

    if sales in (0, None):
        return None

    return round((operating_profit / sales) * 100, 2)


def return_on_equity(net_profit, equity_capital, reserves,):
    """
    Return on Equity (%)
    """

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return round((net_profit / equity) * 100, 2)


def return_on_capital_employed(operating_profit, equity_capital, reserves, borrowings,):
    """
    Return on Capital Employed (%)
    """

    capital = equity_capital + reserves + borrowings

    if capital <= 0:
        return None

    return round((operating_profit / capital) * 100, 2)


def return_on_assets(net_profit, total_assets,):
    """
    Return on Assets (%)
    """

    if total_assets in (0, None):
        return None

    return round((net_profit / total_assets) * 100, 2)


def opm_matches_source(operating_profit,sales, source_opm, tolerance=1,):
    """
    Compare calculated OPM with source value.

    Returns
    -------
    bool
    """

    calculated = operating_profit_margin(operating_profit,sales,)

    if calculated is None:
        return False

    return abs(calculated - source_opm) <= tolerance


def ebit_margin(operating_profit, depreciation, sales):
    """
    EBIT Margin (%)

    Formula:
        ((Operating Profit - Depreciation) / Sales) * 100

    Returns
    -------
    float | None
    """

    if sales is None or sales == 0:
        return None

    ebit = operating_profit - depreciation

    return round((ebit / sales) * 100, 2)

def debt_to_equity(borrowings, equity_capital, reserves):
    """
    Debt-to-Equity Ratio

    Formula:
        Borrowings / (Equity Capital + Reserves)

    Rules
    -----
    • Return 0 if borrowings = 0
    • Return None if equity <= 0
    """

    if borrowings == 0:
        return 0

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return round(borrowings / equity, 2)


def high_leverage_flag(de_ratio, broad_sector):
    """
    High Leverage Flag

    True only if:
    • D/E > 5
    • Company is NOT in Financials
    """

    if de_ratio is None:
        return False

    return (
        de_ratio > 5
        and str(broad_sector).strip().lower() != "financials"
    )


def interest_coverage_ratio(operating_profit, other_income, interest):
    """
    Interest Coverage Ratio

    Formula:
        (Operating Profit + Other Income) / Interest

    Rules
    -----
    Return None if interest = 0
    """

    if interest == 0:
        return None

    return round((operating_profit + other_income) / interest, 2)


def icr_label(icr):
    """
    Display label for Interest Coverage.

    None -> Debt Free
    """

    if icr is None:
        return "Debt Free"

    return ""


def icr_warning_flag(icr):
    """
    Warning when ICR < 1.5
    """

    if icr is None:
        return False

    return icr < 1.5


def net_debt(borrowings, investments):
    """
    Net Debt

    Formula
    -------
    Borrowings - Investments
    """

    return round(borrowings - investments, 2)


def asset_turnover(sales, total_assets):
    """
    Asset Turnover

    Formula
    -------
    Sales / Total Assets

    Rules
    -----
    Return None if total_assets = 0
    """

    if total_assets in (0, None):
        return None

    return round(sales / total_assets, 2)

def earnings_per_share(net_profit, equity_capital):
    """
    Earnings Per Share (EPS)

    Formula
    -------
    Net Profit / Equity Capital

    Returns
    -------
    float | None
    """

    if equity_capital in (None, 0):
        return None

    return round(net_profit / equity_capital, 2)

def book_value_per_share(equity_capital, reserves):
    """
    Book Value Per Share

    Formula
    -------
    (Equity Capital + Reserves) / Equity Capital

    Returns
    -------
    float | None
    """

    if equity_capital in (None, 0):
        return None

    return round(
        (equity_capital + reserves) / equity_capital,
        2,
    )

def dividend_payout_ratio(dividend_payout, net_profit):
    """
    Dividend Payout Ratio (%)

    Formula
    -------
    Dividend Payout / Net Profit × 100

    Returns
    -------
    float | None
    """

    if net_profit in (None, 0):
        return None

    return round(
        (dividend_payout / net_profit) * 100,
        2,
    )

def earnings_per_share(net_profit, equity_capital):
    """
    Earnings Per Share

    Formula:
        Net Profit / Equity Capital
    """

    if equity_capital in (None, 0):
        return None

    return round(net_profit / equity_capital, 2)


def book_value_per_share(equity_capital, reserves):
    """
    Book Value Per Share

    Formula:
        (Equity Capital + Reserves) / Equity Capital
    """

    if equity_capital in (None, 0):
        return None

    return round((equity_capital + reserves) / equity_capital, 2)


def dividend_payout_ratio(dividend_amount, net_profit):
    """
    Dividend Payout Ratio %

    Formula:
        Dividend / Net Profit × 100
    """

    if net_profit in (None, 0):
        return None

    return round((dividend_amount / net_profit) * 100, 2)

def composite_quality_score(
    roe,
    roce,
    revenue_cagr,
    debt_to_equity,
):
    """
    Composite Quality Score (0-100)

    Weightage
    ---------
    ROE              30
    ROCE             30
    Revenue CAGR     20
    Debt to Equity   20
    """

    score = 0

    # ROE
    if roe is not None:
        if roe >= 20:
            score += 30
        elif roe >= 15:
            score += 20
        elif roe >= 10:
            score += 10

    # ROCE
    if roce is not None:
        if roce >= 20:
            score += 30
        elif roce >= 15:
            score += 20
        elif roce >= 10:
            score += 10

    # Revenue CAGR
    if revenue_cagr is not None:
        if revenue_cagr >= 15:
            score += 20
        elif revenue_cagr >= 10:
            score += 15
        elif revenue_cagr >= 5:
            score += 10

    # Debt to Equity
    if debt_to_equity is not None:
        if debt_to_equity <= 0.5:
            score += 20
        elif debt_to_equity <= 1:
            score += 15
        elif debt_to_equity <= 2:
            score += 10

    return score