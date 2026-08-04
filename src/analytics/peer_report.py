import pandas as pd
from src.analytics.radar import (
    load_data,
    merge_peer_groups,
    normalize_radar_metrics,
)


METRICS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5y",
    "revenue_cagr_5y",
    "composite_quality_score",
]


def build_company_peer_report(df, company_id):
    """
    Build a peer comparison report for one company.
    """

    company = df[df["company_id"] == company_id]

    if company.empty:
        return None

    peer_group = company.iloc[0]["peer_group_name"]

    if pd.isna(peer_group):
        return None

    peers = df[
        df["peer_group_name"] == peer_group
    ]

    rows = []

    for metric in METRICS:

        company_value = company.iloc[0][metric]

        peer_average = peers[metric].mean()

        difference = company_value - peer_average

        if difference > 0:
            status = "Above Peer"
        elif difference < 0:
            status = "Below Peer"
        else:
            status = "At Peer"

        rows.append(
            {
                "company_id": company_id,
                "peer_group": peer_group,
                "metric": metric,
                "company_value": round(company_value, 2),
                "peer_average": round(peer_average, 2),
                "difference": round(difference, 2),
                "status": status,
            }
        )

    return pd.DataFrame(rows)

if __name__ == "__main__":

    ratios, peers = load_data()

    df = merge_peer_groups(
        ratios,
        peers,
    )

    latest_year = df["year"].max()

    latest_df = df[
        df["year"] == latest_year
    ].copy()

    latest_df = normalize_radar_metrics(
        latest_df
    )

    report = build_company_peer_report(
        latest_df,
        "TCS",
    )

    print(report)