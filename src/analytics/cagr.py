import math


def calculate_cagr(start_value, end_value, years):
    """
    Calculate CAGR.

    Returns
    -------
    (cagr_value, flag)

    Flags
    -----
    None
    DECLINE_TO_LOSS
    TURNAROUND
    BOTH_NEGATIVE
    ZERO_BASE
    INSUFFICIENT
    """

    if years <= 0:
        return None, "INSUFFICIENT"

    if start_value is None or end_value is None:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value > 0:

        cagr = (
            (end_value / start_value) ** (1 / years) - 1
        ) * 100

        return round(cagr, 2), None

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    return None, "INSUFFICIENT"

def revenue_cagr(df, years):
    """
    Calculate Revenue CAGR for the last N years.

    Returns
    -------
    (cagr, flag)
    """

    df = df.sort_values("year")

    if len(df) < years + 1:
        return None, "INSUFFICIENT"

    start = df.iloc[-(years + 1)]["sales"]
    end = df.iloc[-1]["sales"]

    return calculate_cagr(start, end, years)


def pat_cagr(df, years):
    """
    Calculate PAT CAGR for the last N years.

    Returns
    -------
    (cagr, flag)
    """

    df = df.sort_values("year")

    if len(df) < years + 1:
        return None, "INSUFFICIENT"

    start = df.iloc[-(years + 1)]["net_profit"]
    end = df.iloc[-1]["net_profit"]

    return calculate_cagr(start, end, years)


def eps_cagr(df, years):
    """
    Calculate EPS CAGR for the last N years.

    Returns
    -------
    (cagr, flag)
    """

    df = df.sort_values("year")

    if len(df) < years + 1:
        return None, "INSUFFICIENT"

    start = df.iloc[-(years + 1)]["eps"]
    end = df.iloc[-1]["eps"]

    return calculate_cagr(start, end, years)