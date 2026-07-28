import sqlite3
import pandas as pd
import os

DB_PATH = "data/nifty100.db"
OUTPUT_DIR = "outputs"


# ---------------------------------------------------------
# Save Financial Ratios
# ---------------------------------------------------------
def save_financial_ratios(df):
    """
    Replace the financial_ratios table
    with newly calculated KPI values.
    """

    columns = [
        "company_id",
        "year",

        # Profitability
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "return_on_assets_pct",

        # Leverage
        "debt_to_equity",
        "interest_coverage",
        "net_debt_cr",

        # Efficiency
        "asset_turnover",

        # Per Share
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",

        # Cash Flow
        "free_cash_flow_cr",
        "capex_intensity_pct",
        "capex_intensity_label",
        "fcf_conversion_pct",
        "capital_allocation_pattern",

        # CAGR
        "revenue_cagr_5y",
        "pat_cagr_5y",
        "eps_cagr_5y",

        # Composite
        "composite_quality_score",
        "capex_cr"
    ]

    conn = sqlite3.connect(DB_PATH)

    (
        df[columns]
        .sort_values(["company_id", "year"])
        .reset_index(drop=True)
        .to_sql(
            "financial_ratios",
            conn,
            if_exists="replace",
            index=False,
        )
    )

    conn.close()

    print(f"Saved {len(df)} rows → financial_ratios")


# ---------------------------------------------------------
# Save Company Growth Metrics
# ---------------------------------------------------------
def save_company_growth(df):
    """
    Replace the company_growth_metrics table
    with newly calculated CAGR metrics.
    """

    columns = [
        "company_id",

        "revenue_cagr_3y",
        "revenue_cagr_5y",
        "revenue_cagr_10y",

        "pat_cagr_3y",
        "pat_cagr_5y",

        "eps_cagr_5y",

        "cfo_quality_score",
        "cfo_quality_label",
    ]

    conn = sqlite3.connect(DB_PATH)

    (
        df[columns]
        .sort_values("company_id")
        .reset_index(drop=True)
        .to_sql(
            "company_growth_metrics",
            conn,
            if_exists="replace",
            index=False,
        )
    )

    conn.close()

    print(f"Saved {len(df)} rows → company_growth_metrics")


# ---------------------------------------------------------
# Save Capital Allocation Report
# ---------------------------------------------------------
def save_capital_allocation(df):
    """
    Export Capital Allocation report.

    Output:
        output/capital_allocation.csv
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    report = pd.DataFrame({
        "company_id": df["company_id"],
        "year": df["year"],

        "cfo_sign": df["operating_activity"].apply(
            lambda x: "+" if pd.notna(x) and x > 0 else "-"
        ),

        "cfi_sign": df["investing_activity"].apply(
            lambda x: "+" if pd.notna(x) and x > 0 else "-"
        ),

        "cff_sign": df["financing_activity"].apply(
            lambda x: "+" if pd.notna(x) and x > 0 else "-"
        ),

        "pattern_label": df["capital_allocation_pattern"],
    })

    filepath = os.path.join(
        OUTPUT_DIR,
        "capital_allocation.csv",
    )

    report.to_csv(
        filepath,
        index=False,
    )

    print(f"Saved {len(report)} rows → {filepath}")