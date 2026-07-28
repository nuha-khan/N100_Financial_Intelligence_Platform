import sqlite3
import pandas as pd

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage_ratio,
    net_debt,
    asset_turnover,
    earnings_per_share,
    book_value_per_share,
    dividend_payout_ratio,
    high_leverage_flag,
    icr_label,
    icr_warning_flag,
    composite_quality_score,
)

from src.analytics.cagr import (
    revenue_cagr,
    pat_cagr,
    eps_cagr,
)

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    capital_allocation_pattern,
)

from src.analytics.edge_case_logger import (
    log_ratio_edge_cases,
)

from src.analytics.save_results import (
    save_financial_ratios,
    save_company_growth,
    save_capital_allocation,
)

DB_PATH = "data/nifty100.db"


# ---------------------------------------------------------
# Load required tables
# ---------------------------------------------------------
def load_tables():
    """Load all required SQLite tables."""

    conn = sqlite3.connect(DB_PATH)

    required_tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "market_cap",
        "sectors",
    ]

    tables = {}

    for table in required_tables:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)

        if table in {"profitandloss", "balancesheet", "cashflow"}:
            df = (
                df.sort_values("id")
                  .drop_duplicates(["company_id", "year"], keep="first")
                  .reset_index(drop=True)
            )

        tables[table] = df
        print(f"{table:<20}{len(df)} rows")

    conn.close()
    return tables


# ---------------------------------------------------------
# Merge tables
# ---------------------------------------------------------
def merge_tables(tables):
    """Create one company-year dataframe for KPI computation."""

    df = tables["profitandloss"].copy()

    print("\nMerge diagnostics")
    print("-" * 60)

    diagnostics = [
        ("Profit & Loss", df),
    ]

    df = df.merge(
        tables["balancesheet"].drop(columns="id"),
        on=["company_id", "year"],
        how="left",
    )
    diagnostics.append(("Balance Sheet", df))

    df = df.merge(
        tables["cashflow"].drop(columns="id"),
        on=["company_id", "year"],
        how="left",
    )
    diagnostics.append(("Cash Flow", df))

    df = df.merge(
        tables["market_cap"].drop(columns="id"),
        on=["company_id", "year"],
        how="left",
    )
    diagnostics.append(("Market Cap", df))

    df = df.merge(
        tables["companies"],
        left_on="company_id",
        right_on="id",
        how="left",
        suffixes=("", "_company"),
    )
    diagnostics.append(("Companies", df))

    df = df.merge(
        tables["sectors"],
        on="company_id",
        how="left",
    )
    diagnostics.append(("Sectors", df))

    for name, frame in diagnostics:
        duplicates = frame[["company_id", "year"]].duplicated().sum()
        print(f"{name:<18}: rows={len(frame):4} | duplicates={duplicates}")

    print(f"\nMerged rows : {len(df)}")
    print(f"Merged cols : {len(df.columns)}")

    return df

def compute_financial_ratios(df):
    """
    Compute all financial KPIs for every company-year.

    Returns
    -------
    DataFrame
        DataFrame ready to write into financial_ratios table.
    """

    ratios = df.copy()

    # ---------------------------------------------------------
    # Profitability KPIs
    # ---------------------------------------------------------

    ratios["net_profit_margin_pct"] = ratios.apply(
        lambda r: net_profit_margin(
            r["net_profit"],
            r["sales"],
        ),
        axis=1,
    )

    ratios["operating_profit_margin_pct"] = ratios.apply(
        lambda r: operating_profit_margin(
            r["operating_profit"],
            r["sales"],
        ),
        axis=1,
    )

    ratios["return_on_equity_pct"] = ratios.apply(
        lambda r: return_on_equity(
            r["net_profit"],
            r["equity_capital"],
            r["reserves"],
        ),
        axis=1,
    )

    ratios["return_on_capital_employed_pct"] = ratios.apply(
        lambda r: return_on_capital_employed(
            r["operating_profit"],
            r["equity_capital"],
            r["reserves"],
            r["borrowings"],
        ),
        axis=1,
    )

    ratios["return_on_assets_pct"] = ratios.apply(
        lambda r: return_on_assets(
            r["net_profit"],
            r["total_assets"],
        ),
        axis=1,
    )

    # ---------------------------------------------------------
    # Leverage KPIs
    # ---------------------------------------------------------

    ratios["debt_to_equity"] = ratios.apply(
        lambda r: debt_to_equity(
            r["borrowings"],
            r["equity_capital"],
            r["reserves"],
        ),
        axis=1,
    )

    ratios["high_leverage_flag"] = ratios.apply(
        lambda r: high_leverage_flag(
            r["debt_to_equity"],
            r["broad_sector"],
        ),
        axis=1,
    )

    ratios["interest_coverage"] = ratios.apply(
        lambda r: interest_coverage_ratio(
            r["operating_profit"],
            r["other_income"],
            r["interest"],
        ),
        axis=1,
    )

    ratios["icr_label"] = ratios["interest_coverage"].apply(icr_label)

    ratios["icr_warning_flag"] = ratios["interest_coverage"].apply(
        icr_warning_flag
    )

    ratios["net_debt_cr"] = ratios.apply(
        lambda r: net_debt(
            r["borrowings"],
            r["investments"],
        ),
        axis=1,
    )

    # ---------------------------------------------------------
    # Efficiency KPIs
    # ---------------------------------------------------------

    ratios["asset_turnover"] = ratios.apply(
        lambda r: asset_turnover(
            r["sales"],
            r["total_assets"],
        ),
        axis=1,
    )

    # ---------------------------------------------------------
    # Per Share KPIs
    # ---------------------------------------------------------

    # Use dataset value
    ratios["earnings_per_share"] = ratios["eps"]

    # Compute only Book Value Per Share
    ratios["book_value_per_share"] = ratios.apply(
        lambda r: book_value_per_share(
            r["equity_capital"],
            r["reserves"],
        ),
        axis=1,
    )

    # Use dataset value
    ratios["dividend_payout_ratio_pct"] = ratios["dividend_payout"]

    # Existing values stored directly
    ratios["total_debt_cr"] = ratios["borrowings"]
    ratios["cash_from_operations_cr"] = ratios["operating_activity"]

    # ---------------------------------------------------------
    # Cash Flow KPIs
    # ---------------------------------------------------------

    ratios["free_cash_flow_cr"] = ratios.apply(
        lambda r: free_cash_flow(
            r["operating_activity"],
            r["investing_activity"],
        ),
        axis=1,
    )

    capex = ratios.apply(
        lambda r: capex_intensity(
            r["investing_activity"],
            r["sales"],
        ),
        axis=1,
    )

    ratios["capex_intensity_pct"] = capex.apply(lambda x: x[0])
    ratios["capex_intensity_label"] = capex.apply(lambda x: x[1])

    ratios["fcf_conversion_pct"] = ratios.apply(
        lambda r: fcf_conversion_rate(
            r["operating_activity"],
            r["investing_activity"],
            r["operating_profit"],
        ),
        axis=1,
    )

    ratios["capital_allocation_pattern"] = ratios.apply(
        lambda r: capital_allocation_pattern(
            r["operating_activity"],
            r["investing_activity"],
            r["financing_activity"],
        ),
        axis=1,
    )
    ratios["capex_cr"] = ratios["investing_activity"].abs()

    return ratios

def compute_company_cagrs(merged_df):
    """
    Compute company-level CAGR metrics.

    Returns
    -------
    DataFrame
    """

    cagr_rows = []

    grouped = merged_df.groupby("company_id")

    for company_id, company_df in grouped:

        company_df = company_df.sort_values("year")

        rev3, rev3_flag = revenue_cagr(company_df, 3)
        rev5, rev5_flag = revenue_cagr(company_df, 5)
        rev10, rev10_flag = revenue_cagr(company_df, 10)

        pat3, pat3_flag = pat_cagr(company_df, 3)
        pat5, pat5_flag = pat_cagr(company_df, 5)

        eps5, eps5_flag = eps_cagr(company_df, 5)
        cfo_score, cfo_label = cfo_quality_score(company_df)

        latest_year = company_df["year"].max()

        cagr_rows.append(
            {
                "company_id": company_id,
                "year": latest_year,

                "revenue_cagr_3y": rev3,
                "revenue_cagr_5y": rev5,
                "revenue_cagr_10y": rev10,

                "pat_cagr_3y": pat3,
                "pat_cagr_5y": pat5,

                "eps_cagr_5y": eps5,

                "revenue_flag": rev10_flag or rev5_flag or rev3_flag,
                "pat_flag": pat5_flag or pat3_flag,
                "eps_flag": eps5_flag,
                "cfo_quality_score": cfo_score,
                "cfo_quality_label": cfo_label,
            }
        )

    return pd.DataFrame(cagr_rows)

# ---------------------------------------------------------
# Driver
# ---------------------------------------------------------
if __name__ == "__main__":

    tables = load_tables()

    merged_df = merge_tables(tables)
    print(
merged_df.loc[
    merged_df.company_id == "ABB",
    [
        "company_name",
        "year",
        "net_profit",
        "equity_capital",
        "reserves",
        "total_assets",
        "total_liabilities",
    ]
]
)
    print(merged_df.columns.tolist())
    ratios_df = compute_financial_ratios(merged_df)
    cagr_df = compute_company_cagrs(merged_df)

    # Merge company-level CAGR metrics into financial ratios
    ratios_df = ratios_df.merge(
        cagr_df[
            [
                "company_id",
                "revenue_cagr_5y",
                "pat_cagr_5y",
                "eps_cagr_5y",
            ]
        ],
        on="company_id",
        how="left",
    )
    ratios_df["composite_quality_score"] = ratios_df.apply(
    lambda r: composite_quality_score(
        r["return_on_equity_pct"],
        r["return_on_capital_employed_pct"],
        r["revenue_cagr_5y"],
        r["debt_to_equity"],
    ),
    axis=1,
    )

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    print(
    ratios_df.loc[
        ratios_df["company_id"] == "BEL",
        [
            "company_id",
            "year",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "book_value_per_share",
            "earnings_per_share",
            "debt_to_equity",
            "composite_quality_score",
        ],
    ].to_string(index=False)
)

    # Save outputs
    save_company_growth(cagr_df)
    save_financial_ratios(ratios_df)
    save_capital_allocation(ratios_df)

    log_ratio_edge_cases(merged_df, ratios_df)

    print("\nRatio Engine Summary")
    print("-" * 60)
    print(f"Company-Year Records Processed : {len(ratios_df):,}")
    print(f"Companies Processed            : {len(cagr_df):,}")
    print("Financial Ratios Table         : financial_ratios")
    print("Company Growth Table           : company_growth_metrics")
    print("Capital Allocation Report      : outputs/capital_allocation.csv")
    print("\n✓ Financial ratios computed successfully.")
    print("✓ Company CAGR metrics computed successfully.")
    print("✓ Capital allocation report generated.")
    print("✓ Results saved to SQLite successfully.")
    print("✓ Ratio Engine completed successfully.")