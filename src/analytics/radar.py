import sqlite3
import pandas as pd
from src.screener.scoring import normalize_metric
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

DB_PATH = "data/nifty100.db"
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
DISPLAY_LABELS = [
    "ROE",
    "ROCE",
    "Net Profit\nMargin",
    "Debt /\nEquity",
    "FCF",
    "PAT CAGR\n(5Y)",
    "Revenue CAGR\n(5Y)",
    "Composite\nScore",
]
DISPLAY_COLUMNS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5y",
    "revenue_cagr_5y",
    "composite_quality_score",
]

def load_data():
    """
    Load financial ratios and peer groups from SQLite.
    """

    conn = sqlite3.connect(DB_PATH)

    financial_ratios = pd.read_sql(
        "SELECT * FROM financial_ratios",
        conn,
    )

    peer_groups = pd.read_sql(
        "SELECT * FROM peer_groups",
        conn,
    )

    conn.close()

    return financial_ratios, peer_groups


def merge_peer_groups(financial_ratios, peer_groups):
    """
    Attach peer group information to financial ratios.
    """

    df = financial_ratios.merge(
        peer_groups.drop(columns="id"),
        on="company_id",
        how="left",
    )

    return df

def get_company_and_peer_average(df, company_id):
    """
    Returns one company's latest values
    and the average values of its peer group.
    """

    company = df[df["company_id"] == company_id]

    if company.empty:
        return None, None

    # latest available year
    latest_year = company["year"].max()

    company = company[company["year"] == latest_year]

    peer_group = company.iloc[0]["peer_group_name"]

    if pd.isna(peer_group):
        print(f"{company_id} has no peer group assigned.")
        return None, None

    peers = df[
        (df["peer_group_name"] == peer_group)
        &
        (df["year"] == latest_year)
    ]

    company_values = company[METRICS].iloc[0]

    peer_average = peers[METRICS].mean()

    return company_values, peer_average

def normalize_radar_metrics(df):
    """
    Normalize all radar metrics to a common 0–100 scale.
    """

    radar_df = df.copy()

    for metric in METRICS:

        higher_is_better = metric != "debt_to_equity"

        radar_df[metric] = normalize_metric(
            radar_df[metric],
            higher_is_better=higher_is_better,
        )

    return radar_df

def prepare_radar_data(df, company_id):
    """
    Prepare normalized company metrics and peer-group average
    for the latest available year.
    """

    company = df[df["company_id"] == company_id]

    if company.empty:
        return None, None

    latest_year = company["year"].max()

    company = company[company["year"] == latest_year]

    peer_group = company["peer_group_name"].iloc[0]

    if pd.isna(peer_group):
        return None, None

    peer_df = df[
        (df["peer_group_name"] == peer_group)
        &
        (df["year"] == latest_year)
    ]

    company_values = company[DISPLAY_COLUMNS].iloc[0]

    peer_values = peer_df[DISPLAY_COLUMNS].mean()

    return company_values, peer_values

def plot_radar_chart(company_id, company_values, peer_values):
    """
    Generate a radar chart comparing a company
    against its peer-group average.
    """

    labels = DISPLAY_LABELS

    company = company_values.values.tolist()
    peer = peer_values.values.tolist()

    # Close the polygon
    company += company[:1]
    peer += peer[:1]

    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False,
    ).tolist()

    angles += angles[:1]

    fig = plt.figure(figsize=(9, 9))

    ax = plt.subplot(111, polar=True)

    # Start at the top and move clockwise
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Company
    ax.plot(
        angles,
        company,
        color="#1565C0",
        linewidth=2.5,
        label=company_id,
    )

    ax.fill(
        angles,
        company,
        color="#42A5F5",
        alpha=0.30,
    )

    # Peer Average
    ax.plot(
        angles,
        peer,
        color="#F57C00",
        linestyle="--",
        linewidth=2.5,
        label="Peer Average",
    )

    ax.set_xticks(angles[:-1])

    ax.set_xticklabels(
        labels,
        fontsize=10,
        fontweight="bold",
    )

    ax.set_ylim(0, 100)

    ax.set_yticks([25, 50, 75, 100])

    ax.set_yticklabels(
        ["25", "50", "75", "100"],
        fontsize=8,
    )

    ax.grid(
        color="grey",
        linestyle="--",
        linewidth=0.8,
        alpha=0.35,
    )

    plt.title(
        f"{company_id} vs Peer Group Average",
        fontsize=16,
        fontweight="bold",
        pad=25,
    )

    plt.legend(
        loc="upper right",
        bbox_to_anchor=(1.18, 1.12),
        fontsize=10,
        frameon=True,
    )

    output_dir = Path("reports/radar_charts")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.savefig(
        output_dir / f"{company_id}_radar.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

def generate_all_radar_charts(df):
    """
    Generate radar charts for every company
    using the latest available year.
    """

    latest = (
        df.sort_values("year")
          .groupby("company_id")
          .tail(1)
    )

    print(f"Generating charts for {len(latest)} companies...")

    generated = 0

    for company in latest["company_id"]:

        company_values, peer_values = prepare_radar_data(
            df,
            company,
        )

        if company_values is None:
            continue

        plot_radar_chart(
            company,
            company_values,
            peer_values,
        )

        generated += 1

    print(f"Generated {generated} radar charts.")

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

    generate_all_radar_charts(
        latest_df
    )

    print("Radar charts generated successfully.")