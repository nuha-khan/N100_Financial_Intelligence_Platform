import pandas as pd


def winsorize(series, lower=0.10, upper=0.90):
    """
    Cap extreme values at given percentiles.
    """

    s = pd.to_numeric(series, errors="coerce")

    low = s.quantile(lower)
    high = s.quantile(upper)

    return s.clip(lower=low, upper=high)


def normalize_metric(series, higher_is_better=True):
    """
    Normalize metric to 0-100 after winsorization.
    """

    s = winsorize(series)

    minimum = s.min()
    maximum = s.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(50.0, index=s.index)

    if maximum == minimum:
        return pd.Series(50.0, index=s.index)

    score = ((s - minimum) / (maximum - minimum)) * 100

    if not higher_is_better:
        score = 100 - score

    return score.fillna(50).round(2)


def sector_relative_score(df, metric, higher_is_better=True):
    """
    Normalize one metric separately inside each sector.
    """

    scores = pd.Series(index=df.index, dtype=float)

    for sector, group in df.groupby("broad_sector"):

        scores.loc[group.index] = normalize_metric(
            group[metric],
            higher_is_better=higher_is_better,
        )

    return scores.fillna(50)


def compute_composite_score(df):
    """
    Sprint-3 Composite Quality Score

    Profitability : 35%
    Cash Quality  : 30%
    Growth        : 20%
    Leverage      : 15%
    """

    df = df.copy()

    # ---------------- Profitability ----------------

    df["roe_score"] = sector_relative_score(
        df,
        "return_on_equity_pct",
    )

    df["roce_score"] = sector_relative_score(
        df,
        "return_on_capital_employed_pct",
    )

    df["npm_score"] = sector_relative_score(
        df,
        "net_profit_margin_pct",
    )

    # ---------------- Cash Quality ----------------

    df["fcf_score"] = sector_relative_score(
        df,
        "free_cash_flow_cr",
    )

    df["cashflow_score"] = sector_relative_score(
        df,
        "cash_from_operations_cr",
    )

    # ---------------- Growth ----------------

    df["revenue_score"] = sector_relative_score(
        df,
        "revenue_cagr_5y",
    )

    df["pat_score"] = sector_relative_score(
        df,
        "pat_cagr_5y",
    )

    # ---------------- Leverage ----------------

    df["de_score"] = sector_relative_score(
        df,
        "debt_to_equity",
        higher_is_better=False,
    )

    # ---------------- Final Score ----------------

    df["composite_quality_score"] = (
          0.15 * df["roe_score"]
        + 0.10 * df["roce_score"]
        + 0.10 * df["npm_score"]
        + 0.15 * df["fcf_score"]
        + 0.15 * df["cashflow_score"]
        + 0.10 * df["revenue_score"]
        + 0.10 * df["pat_score"]
        + 0.15 * df["de_score"]
    ).round().astype(int)

    return df