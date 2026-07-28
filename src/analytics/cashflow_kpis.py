"""
Cash Flow KPI calculations.

All functions are row-level calculations and are intended to be
used inside compute_financial_ratios().
"""


def free_cash_flow(operating_activity, investing_activity):
    """
    Free Cash Flow (Cr)

    Formula
    -------
    Operating Cash Flow + Investing Cash Flow

    Returns
    -------
    float | None
    """

    if operating_activity is None or investing_activity is None:
        return None

    return round(operating_activity + investing_activity, 2)


def capex_intensity(investing_activity, sales):
    """
    CapEx Intensity (%)

    Formula
    -------
    |Investing Activity| / Sales × 100

    Returns
    -------
    (value, label)
    """

    if investing_activity is None or sales in (None, 0):
        return None, None

    intensity = (abs(investing_activity) / sales) * 100

    if intensity < 3:
        label = "Asset Light"
    elif intensity <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return round(intensity, 2), label


def fcf_conversion_rate(
    operating_activity,
    investing_activity,
    operating_profit,
):
    """
    FCF Conversion Rate (%)

    Formula
    -------
    Free Cash Flow / Operating Profit × 100

    Returns
    -------
    float | None
    """

    if operating_profit in (None, 0):
        return None

    fcf = free_cash_flow(
        operating_activity,
        investing_activity,
    )

    if fcf is None:
        return None

    return round((fcf / operating_profit) * 100, 2)


def capital_allocation_pattern(
    operating_activity,
    investing_activity,
    financing_activity,
):
    """
    Capital Allocation Pattern

    Returns
    -------
    str
    """

    if (
        operating_activity is None
        or investing_activity is None
        or financing_activity is None
    ):
        return "Unknown"

    cfo = operating_activity > 0
    cfi = investing_activity > 0
    cff = financing_activity > 0

    if cfo and (not cfi) and (not cff):
        return "Reinvestor"

    if cfo and cfi and (not cff):
        return "Liquidating Assets"

    if (not cfo) and cfi and cff:
        return "Distress Signal"

    if (not cfo) and (not cfi) and cff:
        return "Growth Funded by Debt"

    if cfo and cfi and cff:
        return "Cash Accumulator"

    if (not cfo) and (not cfi) and (not cff):
        return "Pre-Revenue"

    if cfo and (not cfi) and cff:
        return "Mixed"

    return "Unknown"


def cfo_quality_score(company_df):
    """
    Company-level CFO Quality Score

    Formula
    -------
    Average (Operating Cash Flow / Net Profit)
    over the latest 5 financial years.

    Returns
    -------
    (score, label)
    """

    company_df = company_df.sort_values("year")

    if len(company_df) < 5:
        return None, "INSUFFICIENT"

    recent = company_df.tail(5)

    ratios = []

    for _, row in recent.iterrows():

        cfo = row["operating_activity"]
        pat = row["net_profit"]

        if cfo is None or pat in (None, 0):
            continue

        ratios.append(cfo / pat)

    if not ratios:
        return None, "INSUFFICIENT"

    score = sum(ratios) / len(ratios)

    if score > 1:
        label = "High Quality"
    elif score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return round(score, 2), label