"""
Day 37 — Cluster Profiling & Statistics

Profiles the five KMeans clusters, generates a 10-KPI Pearson
correlation heatmap, detects sector-level statistical outliers,
and generates portfolio-level KPI statistics.
"""

from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import zscore


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "outputs"
REPORTS_DIR = BASE_DIR / "reports"

CLUSTER_LABELS_OUTPUT = OUTPUT_DIR / "cluster_labels.csv"
CLUSTER_PROFILES_OUTPUT = OUTPUT_DIR / "cluster_profiles.csv"
OUTLIER_OUTPUT = OUTPUT_DIR / "outlier_report.csv"
PORTFOLIO_STATS_OUTPUT = OUTPUT_DIR / "portfolio_stats.csv"

CORRELATION_OUTPUT = REPORTS_DIR / "correlation_heatmap.png"


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

CLUSTER_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

CORRELATION_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "interest_coverage",
    "asset_turnover",
    "earnings_per_share",
    "dividend_payout_ratio_pct",
]


# ---------------------------------------------------------------------
# DATABASE LOADING
# ---------------------------------------------------------------------

def load_data():
    """Load clustering, ratio, sector and growth data from SQLite."""

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name
        FROM companies
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector,
            sub_sector,
            market_cap_category
        FROM sectors
        """,
        conn,
    )

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            asset_turnover,
            earnings_per_share,
            dividend_payout_ratio_pct
        FROM financial_ratios
        WHERE year IS NOT NULL
        """,
        conn,
    )

    growth = pd.read_sql_query(
        """
        SELECT
            company_id,
            revenue_cagr_5y,
            eps_cagr_5y
        FROM company_growth_metrics
        """,
        conn,
    )

    conn.close()

    return companies, sectors, ratios, growth


# ---------------------------------------------------------------------
# CLEAN LATEST-YEAR RATIO DATA
# ---------------------------------------------------------------------

def prepare_latest_data(companies, sectors, ratios, growth):
    """
    Create one clean latest-year record per company.

    Duplicate company/year records are collapsed using the median.
    """

    ratio_features = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "earnings_per_share",
        "dividend_payout_ratio_pct",
    ]

    yearly_ratios = (
        ratios.groupby(
            ["company_id", "year"],
            as_index=False,
        )[ratio_features]
        .median()
    )

    # Treat obviously corrupted OPM values consistently with Day 36.
    invalid_opm = (
        yearly_ratios[
            "operating_profit_margin_pct"
        ].abs()
        > 100
    )

    invalid_count = int(invalid_opm.sum())

    if invalid_count:
        print(
            "Invalid OPM values ignored for Day 37: "
            f"{invalid_count}"
        )

        yearly_ratios.loc[
            invalid_opm,
            "operating_profit_margin_pct",
        ] = pd.NA

    latest_ratios = (
        yearly_ratios
        .sort_values(["company_id", "year"])
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    latest_ratios = latest_ratios[
        ["company_id", "year"] + ratio_features
    ]

    # Deduplicate growth metrics by company.
    growth_clean = (
        growth.groupby(
            "company_id",
            as_index=False,
        )[
            [
                "revenue_cagr_5y",
                "eps_cagr_5y",
            ]
        ]
        .median()
    )

    df = companies.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
                "sub_sector",
                "market_cap_category",
            ]
        ],
        on="company_id",
        how="left",
    )

    df = df.merge(
        latest_ratios,
        on="company_id",
        how="left",
    )

    df = df.merge(
        growth_clean,
        on="company_id",
        how="left",
    )

    # ---------------------------------------------------------------
    # FCF CAGR
    #
    # Use the financial ratios table to calculate five-year FCF CAGR.
    # ---------------------------------------------------------------

    fcf_data = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            free_cash_flow_cr
        FROM financial_ratios
        WHERE year IS NOT NULL
        """,
        sqlite3.connect(DB_PATH),
    )

    fcf_yearly = (
        fcf_data.groupby(
            ["company_id", "year"],
            as_index=False,
        )["free_cash_flow_cr"]
        .median()
    )

    fcf_results = []

    for company_id, group in fcf_yearly.groupby(
        "company_id"
    ):
        group = group.sort_values("year")

        latest_year = group["year"].max()
        start_year = latest_year - 5

        start = group[
            group["year"] == start_year
        ]["free_cash_flow_cr"]

        end = group[
            group["year"] == latest_year
        ]["free_cash_flow_cr"]

        if (
            len(start) == 1
            and len(end) == 1
            and pd.notna(start.iloc[0])
            and pd.notna(end.iloc[0])
            and start.iloc[0] > 0
            and end.iloc[0] > 0
        ):
            cagr = (
                (end.iloc[0] / start.iloc[0])
                ** (1 / 5)
                - 1
            ) * 100
        else:
            cagr = pd.NA

        fcf_results.append(
            {
                "company_id": company_id,
                "fcf_cagr_5yr": cagr,
            }
        )

    fcf_cagr = pd.DataFrame(fcf_results)

    df = df.merge(
        fcf_cagr,
        on="company_id",
        how="left",
    )

    df = df.rename(
        columns={
            "revenue_cagr_5y": "revenue_cagr_5yr",
        }
    )

    return df


# ---------------------------------------------------------------------
# CLUSTER PROFILING
# ---------------------------------------------------------------------

def generate_cluster_profiles(df):
    """Generate mean and median statistics for each cluster."""

    print("\nGenerating cluster profiles...")

    labels = pd.read_csv(
        CLUSTER_LABELS_OUTPUT
    )

    if len(labels) != 92:
        raise ValueError(
            "cluster_labels.csv must contain "
            "exactly 92 companies."
        )

    df = df.merge(
        labels[
            [
                "company_id",
                "cluster_id",
                "cluster_name",
            ]
        ],
        on="company_id",
        how="left",
    )

    if df["cluster_id"].isna().any():
        raise ValueError(
            "Some companies are missing cluster assignments."
        )

    mean_profile = (
        df.groupby(
            [
                "cluster_id",
                "cluster_name",
            ]
        )[CLUSTER_FEATURES]
        .mean()
        .add_suffix("_mean")
    )

    median_profile = (
        df.groupby(
            [
                "cluster_id",
                "cluster_name",
            ]
        )[CLUSTER_FEATURES]
        .median()
        .add_suffix("_median")
    )

    profile = mean_profile.join(
        median_profile
    ).reset_index()

    profile = profile.sort_values(
        "cluster_id"
    )

    profile.to_csv(
        CLUSTER_PROFILES_OUTPUT,
        index=False,
    )

    print("\nCLUSTER PROFILES:")
    print(
        profile.round(2).to_string(
            index=False
        )
    )

    return df, profile


# ---------------------------------------------------------------------
# CORRELATION HEATMAP
# ---------------------------------------------------------------------

def generate_correlation_heatmap(df):
    """Generate Pearson correlation heatmap for ten latest-year KPIs."""

    print(
        "\nGenerating correlation heatmap..."
    )

    correlation_data = df[
        CORRELATION_FEATURES
    ].copy()

    # FCF and CAGR values may legitimately be missing.
    # Pearson correlation uses pairwise available observations.
    correlation_data = df[CORRELATION_FEATURES].copy()

    for column in CORRELATION_FEATURES:
        correlation_data[column] = pd.to_numeric(
        correlation_data[column],
        errors="coerce",
    )

    correlation_data = correlation_data.astype(float)

    correlation = correlation_data.corr(method="pearson")

    plt.figure(
        figsize=(13, 10)
    )

    sns.heatmap(
        correlation,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=0.5,
    )

    plt.title(
        "Pearson Correlation Matrix — Latest Year KPIs"
    )

    plt.tight_layout()

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.savefig(
        CORRELATION_OUTPUT,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Correlation heatmap saved: "
        f"{CORRELATION_OUTPUT}"
    )

    return correlation


# ---------------------------------------------------------------------
# OUTLIER DETECTION
# ---------------------------------------------------------------------

def generate_outlier_report(df):
    """
    Detect companies with absolute sector-level Z-score greater than 3.

    Z-scores are calculated independently within each broad sector.
    """

    print(
        "\nGenerating sector-level outlier report..."
    )

    metrics = CORRELATION_FEATURES

    records = []

    for sector, sector_df in df.groupby(
        "broad_sector",
        dropna=False,
    ):

        sector_df = sector_df.copy()

        for metric in metrics:

            values = pd.to_numeric(
                sector_df[metric],
                errors="coerce",
            )

            valid = values.dropna()

            if len(valid) < 3:
                continue

            mean = valid.mean()
            std = valid.std(ddof=0)

            if std == 0 or pd.isna(std):
                continue

            z_scores = (
                values - mean
            ) / std

            flagged = (
                z_scores.abs() > 3
            )

            for idx in sector_df.index[
                flagged.fillna(False)
            ]:

                records.append(
                    {
                        "company_id": sector_df.loc[
                            idx,
                            "company_id",
                        ],
                        "company_name": sector_df.loc[
                            idx,
                            "company_name",
                        ],
                        "broad_sector": sector,
                        "metric": metric,
                        "value": sector_df.loc[
                            idx,
                            metric,
                        ],
                        "z_score": z_scores.loc[
                            idx
                        ],
                        "threshold": 3,
                    }
                )

    columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "metric",
        "value",
        "z_score",
        "threshold",
    ]

    outliers = pd.DataFrame(
        records,
        columns=columns,
    )

    if not outliers.empty:
        outliers = outliers.sort_values(
            [
                "broad_sector",
                "company_id",
                "metric",
            ]
        )

        outliers["z_score"] = (
            outliers["z_score"]
            .round(4)
        )

    outliers.to_csv(
        OUTLIER_OUTPUT,
        index=False,
    )

    print(
        f"Outlier records found : "
        f"{len(outliers)}"
    )

    print(
        f"Outlier report saved : "
        f"{OUTLIER_OUTPUT}"
    )

    return outliers


# ---------------------------------------------------------------------
# PORTFOLIO STATISTICS
# ---------------------------------------------------------------------

def generate_portfolio_stats(df):
    """Generate P10 through P90, mean and standard deviation for KPIs."""

    print(
        "\nGenerating portfolio statistics..."
    )

    records = []

    for metric in CORRELATION_FEATURES:

        values = pd.to_numeric(
            df[metric],
            errors="coerce",
        ).dropna()

        if values.empty:
            continue

        records.append(
            {
                "kpi": metric,
                "p10": values.quantile(0.10),
                "p25": values.quantile(0.25),
                "p50": values.quantile(0.50),
                "p75": values.quantile(0.75),
                "p90": values.quantile(0.90),
                "mean": values.mean(),
                "std": values.std(),
                "company_count": len(values),
            }
        )

    stats = pd.DataFrame(records)

    numeric_columns = [
        "p10",
        "p25",
        "p50",
        "p75",
        "p90",
        "mean",
        "std",
    ]

    stats[numeric_columns] = (
        stats[numeric_columns]
        .round(4)
    )

    stats.to_csv(
        PORTFOLIO_STATS_OUTPUT,
        index=False,
    )

    print("\nPORTFOLIO STATISTICS:")
    print(
        stats.to_string(index=False)
    )

    print(
        f"\nPortfolio statistics saved : "
        f"{PORTFOLIO_STATS_OUTPUT}"
    )

    return stats


# ---------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------

def validate_outputs(
    df,
    profile,
    correlation,
    outliers,
    stats,
):
    """Validate all Day 37 deliverables."""

    print("\n" + "=" * 72)
    print("DAY 37 VALIDATION")
    print("=" * 72)

    # ---------------------------------------------------------------
    # Company count.
    # ---------------------------------------------------------------

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 companies, found {len(df)}."
        )

    if df["company_id"].nunique() != 92:
        raise ValueError(
            "Company IDs are not unique."
        )

    print("PASS — 92 companies represented")

    # ---------------------------------------------------------------
    # Cluster profile validation.
    # ---------------------------------------------------------------

    if len(profile) != 5:
        raise ValueError(
            "Expected five cluster profiles."
        )

    if profile["cluster_id"].nunique() != 5:
        raise ValueError(
            "Expected five unique cluster IDs."
        )

    print(
        "PASS — five cluster profiles generated"
    )

    # ---------------------------------------------------------------
    # Correlation matrix.
    # ---------------------------------------------------------------

    if correlation.shape != (
        10,
        10,
    ):
        raise ValueError(
            "Correlation matrix is not 10 x 10."
        )

    print(
        "PASS — 10 x 10 correlation matrix generated"
    )

    # ---------------------------------------------------------------
    # Portfolio statistics.
    # ---------------------------------------------------------------

    if len(stats) != 10:
        raise ValueError(
            "Expected portfolio statistics "
            "for all 10 KPIs."
        )

    print(
        "PASS — portfolio statistics generated "
        "for 10 KPIs"
    )

    # ---------------------------------------------------------------
    # Files.
    # ---------------------------------------------------------------

    required_files = [
        CLUSTER_PROFILES_OUTPUT,
        CORRELATION_OUTPUT,
        OUTLIER_OUTPUT,
        PORTFOLIO_STATS_OUTPUT,
    ]

    for file_path in required_files:

        if not file_path.exists():
            raise ValueError(
                f"Missing output file: {file_path}"
            )

        if file_path.stat().st_size == 0:
            raise ValueError(
                f"Output file is empty: {file_path}"
            )

        print(
            f"PASS — {file_path.relative_to(BASE_DIR)}"
        )

    print("\nSTATUS: PASS")
    print(
        "Day 37 cluster profiling, correlation, "
        "outlier detection and portfolio statistics "
        "completed successfully."
    )

    print("=" * 72)


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def run_day37():
    """Run the complete Day 37 analytics pipeline."""

    print("=" * 72)
    print(
        "SPRINT 6 — DAY 37 CLUSTER PROFILING & STATISTICS"
    )
    print("=" * 72)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\nLoading database...")

    companies, sectors, ratios, growth = (
        load_data()
    )

    print(
        f"Official companies : {len(companies)}"
    )

    print(
        f"Ratio records      : {len(ratios)}"
    )

    print(
        f"Growth records     : {len(growth)}"
    )

    if len(companies) != 92:
        raise ValueError(
            "Database must contain 92 companies."
        )

    print(
        "\nPreparing latest-year KPI dataset..."
    )

    df = prepare_latest_data(
        companies,
        sectors,
        ratios,
        growth,
    )

    print(
        f"Companies prepared : {len(df)}"
    )

    # ---------------------------------------------------------------
    # Cluster profiles.
    # ---------------------------------------------------------------

    df, profile = generate_cluster_profiles(
        df
    )

    # ---------------------------------------------------------------
    # Correlation heatmap.
    # ---------------------------------------------------------------

    correlation = (
        generate_correlation_heatmap(df)
    )

    # ---------------------------------------------------------------
    # Outliers.
    # ---------------------------------------------------------------

    outliers = generate_outlier_report(
        df
    )

    # ---------------------------------------------------------------
    # Portfolio statistics.
    # ---------------------------------------------------------------

    stats = generate_portfolio_stats(
        df
    )

    # ---------------------------------------------------------------
    # Validation.
    # ---------------------------------------------------------------

    validate_outputs(
        df,
        profile,
        correlation,
        outliers,
        stats,
    )

    return {
        "dataset": df,
        "cluster_profiles": profile,
        "correlation": correlation,
        "outliers": outliers,
        "portfolio_stats": stats,
    }


if __name__ == "__main__":
    run_day37()
