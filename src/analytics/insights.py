import pandas as pd
from pathlib import Path

from src.analytics.peer_report import build_company_peer_report
from src.analytics.radar import (
    load_data,
    merge_peer_groups,
    normalize_radar_metrics,
)

METRIC_NAMES = {
    "return_on_equity_pct": "Return on Equity",
    "return_on_capital_employed_pct": "Return on Capital Employed",
    "net_profit_margin_pct": "Net Profit Margin",
    "debt_to_equity": "Debt to Equity",
    "free_cash_flow_cr": "Free Cash Flow",
    "pat_cagr_5y": "PAT CAGR (5Y)",
    "revenue_cagr_5y": "Revenue CAGR (5Y)",
    "composite_quality_score": "Composite Quality Score",
}


def generate_company_insights(report):
    """
    Generate executive insights from the peer comparison report.
    """

    strengths = []
    weaknesses = []

    for _, row in report.iterrows():

        metric = METRIC_NAMES.get(
            row["metric"],
            row["metric"],
        )

        if row["status"] == "Above Peer":
            strengths.append(metric)

        elif row["status"] == "Below Peer":
            weaknesses.append(metric)

    return {
        "Strengths": strengths,
        "Weaknesses": weaknesses,
    }


def build_summary(company_id, report, insights):
    """
    Build executive summary text.
    """

    peer_group = report.iloc[0]["peer_group"]

    lines = []

    lines.append("=" * 60)
    lines.append("EXECUTIVE INSIGHTS REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Company    : {company_id}")
    lines.append(f"Peer Group : {peer_group}")
    lines.append("")

    lines.append("Strengths")
    lines.append("-" * 30)

    if insights["Strengths"]:
        for item in insights["Strengths"]:
            lines.append(f"✓ {item}")
    else:
        lines.append("None")

    lines.append("")
    lines.append("Weaknesses")
    lines.append("-" * 30)

    if insights["Weaknesses"]:
        for item in insights["Weaknesses"]:
            lines.append(f"• {item}")
    else:
        lines.append("None")

    lines.append("")
    lines.append("Overall Assessment")
    lines.append("-" * 30)

    if len(insights["Strengths"]) > len(insights["Weaknesses"]):
        assessment = (
            "The company outperforms its peer group across most key "
            "financial metrics and demonstrates strong overall quality."
        )

    elif len(insights["Strengths"]) < len(insights["Weaknesses"]):
        assessment = (
            "The company underperforms its peer group in several key "
            "areas and may require further investigation."
        )

    else:
        assessment = (
            "The company performs broadly in line with its peer group, "
            "showing a balanced financial profile."
        )

    lines.append(assessment)

    return "\n".join(lines)


def save_summary(company_id, summary):
    """
    Save executive summary as a text file.
    """

    output_dir = Path("reports/executive_insights")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = output_dir / f"{company_id}_insights.txt"

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(summary)


if __name__ == "__main__":

    ratios, peers = load_data()

    df = merge_peer_groups(ratios,peers)

    latest_year = df["year"].max()

    latest_df = df[df["year"] == latest_year].copy()

    latest_df = normalize_radar_metrics(latest_df,)

    companies = (
        latest_df["company_id"]
        .drop_duplicates()
        .sort_values()
    )

    generated = 0

    for company_id in companies:

        report = build_company_peer_report(latest_df,company_id)

        if report is None:
            continue

        insights = generate_company_insights(report)

        summary = build_summary(company_id,report,insights)

        save_summary(company_id,summary)

        generated += 1

    print(f"Generated {generated} executive insight reports.")