"""
Day 36 — KMeans Financial Clustering

Creates five financial features for all Nifty 100 companies,
handles missing values using sector medians, standardises the
features, runs KMeans clustering, generates an elbow plot,
and saves cluster assignments.
"""

from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORTS_DIR = BASE_DIR / "reports"

CLUSTER_OUTPUT = OUTPUT_DIR / "cluster_labels.csv"
ELBOW_OUTPUT = REPORTS_DIR / "elbow_plot.png"


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

N_CLUSTERS = 5
RANDOM_STATE = 42


# ---------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------

def load_data():
    """Load company, sector, ratio and growth data from SQLite."""

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
            return_on_equity_pct,
            debt_to_equity,
            operating_profit_margin_pct,
            free_cash_flow_cr
        FROM financial_ratios
        WHERE year IS NOT NULL
        """,
        conn,
    )

    growth = pd.read_sql_query(
        """
        SELECT
            company_id,
            revenue_cagr_5y
        FROM company_growth_metrics
        """,
        conn,
    )

    conn.close()

    return companies, sectors, ratios, growth


# ---------------------------------------------------------------------
# FCF CAGR
# ---------------------------------------------------------------------

def calculate_fcf_cagr(ratios):
    """Calculate five-year FCF CAGR for each company."""

    yearly_fcf = (
        ratios.groupby(["company_id", "year"], as_index=False)[
            "free_cash_flow_cr"
        ]
        .mean()
    )

    results = []

    for company_id, group in yearly_fcf.groupby("company_id"):
        group = group.sort_values("year")

        latest_year = group["year"].max()
        start_year = latest_year - 5

        latest_rows = group[group["year"] == latest_year]
        start_rows = group[group["year"] == start_year]

        if latest_rows.empty or start_rows.empty:
            fcf_cagr = None
        else:
            start_fcf = start_rows["free_cash_flow_cr"].iloc[0]
            end_fcf = latest_rows["free_cash_flow_cr"].iloc[0]

            if (
                pd.isna(start_fcf)
                or pd.isna(end_fcf)
                or start_fcf <= 0
                or end_fcf <= 0
            ):
                fcf_cagr = None
            else:
                fcf_cagr = (
                    (end_fcf / start_fcf) ** (1 / 5) - 1
                ) * 100

        results.append(
            {
                "company_id": company_id,
                "fcf_cagr_5yr": fcf_cagr,
            }
        )

    return pd.DataFrame(results)


# ---------------------------------------------------------------------
# BUILD FEATURE DATASET
# ---------------------------------------------------------------------

def build_feature_dataset(companies, sectors, ratios, growth):
    """Build the five-feature clustering dataset."""

    fcf_cagr = calculate_fcf_cagr(ratios)

    # Collapse duplicate company/year records.
    ratio_yearly = (
        ratios.groupby(["company_id", "year"], as_index=False)[
            [
                "return_on_equity_pct",
                "debt_to_equity",
                "operating_profit_margin_pct",
            ]
        ]
        .median()
    )

    # -----------------------------------------------------------------
    # Clean clearly invalid OPM values.
    #
    # The database contains values such as 47971% and -50971%.
    # These are not realistic OPM values and would dominate KMeans.
    #
    # Treat values outside [-100, 100] as invalid and let the
    # sector-median imputation handle them later.
    # -----------------------------------------------------------------

    invalid_opm = (
        ratio_yearly["operating_profit_margin_pct"].abs() > 100
    )

    invalid_count = int(invalid_opm.sum())

    if invalid_count:
        print(
            f"\nInvalid OPM values replaced with NaN : {invalid_count}"
        )

    ratio_yearly.loc[
        invalid_opm,
        "operating_profit_margin_pct",
    ] = pd.NA

    # -----------------------------------------------------------------
    # Keep the latest available year for each company.
    # -----------------------------------------------------------------

    latest_ratios = (
        ratio_yearly
        .sort_values(["company_id", "year"])
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    latest_ratios = latest_ratios[
        [
            "company_id",
            "year",
            "return_on_equity_pct",
            "debt_to_equity",
            "operating_profit_margin_pct",
        ]
    ]

    # -----------------------------------------------------------------
    # Merge company + sector + latest ratios + growth.
    # -----------------------------------------------------------------

    df = companies.merge(
        sectors[["company_id", "broad_sector"]],
        on="company_id",
        how="left",
    )

    df = df.merge(
        latest_ratios,
        on="company_id",
        how="left",
    )

    df = df.merge(
        growth[["company_id", "revenue_cagr_5y"]],
        on="company_id",
        how="left",
    )

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
# SECTOR MEDIAN IMPUTATION
# ---------------------------------------------------------------------

def impute_sector_medians(df):
    """Impute missing feature values using broad-sector medians."""

    df = df.copy()

    print("\nMissing values BEFORE sector imputation:")
    print(df[FEATURES].isna().sum().to_string())

    for feature in FEATURES:

        sector_medians = (
            df.groupby("broad_sector")[feature]
            .transform("median")
        )

        df[feature] = df[feature].fillna(sector_medians)

        # Final global fallback.
        df[feature] = df[feature].fillna(
            df[feature].median()
        )

    print("\nMissing values AFTER sector imputation:")
    print(df[FEATURES].isna().sum().to_string())

    return df


# ---------------------------------------------------------------------
# ELBOW CURVE
# ---------------------------------------------------------------------

def generate_elbow_plot(X):
    """Generate and save the KMeans elbow plot for k=2 through k=10."""

    print("\nGenerating elbow plot...")

    k_values = range(2, 11)
    inertias = []

    for k in k_values:

        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=10,
        )

        model.fit(X)
        inertias.append(model.inertia_)

        print(
            f"k={k}: inertia={model.inertia_:.2f}"
        )

    plt.figure(figsize=(9, 6))

    plt.plot(
        list(k_values),
        inertias,
        marker="o",
    )

    plt.axvline(
        x=N_CLUSTERS,
        linestyle="--",
        label="Selected k = 5",
    )

    plt.title("KMeans Elbow Curve")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.xticks(list(k_values))
    plt.legend()
    plt.grid(True, alpha=0.3)

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.tight_layout()
    plt.savefig(
        ELBOW_OUTPUT,
        dpi=150,
    )
    plt.close()

    print(
        f"\nElbow plot saved: {ELBOW_OUTPUT}"
    )


# ---------------------------------------------------------------------
# CLUSTER NAMES
# ---------------------------------------------------------------------

def assign_cluster_names(df):
    """
    Assign five descriptive names based on cluster profiles.

    The names are generated from the relative characteristics of
    the five clusters rather than from specific company names.
    """

    profile = (
        df.groupby("cluster_id")[FEATURES]
        .mean()
    )

    print("\nCLUSTER PROFILES:")
    print(
        profile.round(2).to_string()
    )

    # ---------------------------------------------------------------
    # Calculate relative scores.
    # ---------------------------------------------------------------

    quality_score = (
        profile["return_on_equity_pct"].rank(pct=True)
        + profile["revenue_cagr_5yr"].rank(pct=True)
        + profile["fcf_cagr_5yr"].rank(pct=True)
        + profile["operating_profit_margin_pct"].rank(pct=True)
        - profile["debt_to_equity"].rank(pct=True)
    )

    growth_score = (
        profile["revenue_cagr_5yr"].rank(pct=True)
        + profile["fcf_cagr_5yr"].rank(pct=True)
    )

    leverage_score = (
        profile["debt_to_equity"].rank(pct=True)
    )

    profitability_score = (
        profile["return_on_equity_pct"].rank(pct=True)
        + profile["operating_profit_margin_pct"].rank(pct=True)
    )

    names = {}

    # ---------------------------------------------------------------
    # 1. Highest overall quality.
    # ---------------------------------------------------------------

    quality_cluster = quality_score.idxmax()

    names[quality_cluster] = (
        "High-Quality Compounders"
    )

    # ---------------------------------------------------------------
    # 2. Highest growth among remaining clusters.
    # ---------------------------------------------------------------

    remaining = [
        c for c in profile.index
        if c not in names
    ]

    if remaining:

        growth_cluster = (
            growth_score.loc[remaining]
            .idxmax()
        )

        names[growth_cluster] = (
            "Emerging Growth"
        )

    # ---------------------------------------------------------------
    # 3. Highest leverage among remaining.
    # ---------------------------------------------------------------

    remaining = [
        c for c in profile.index
        if c not in names
    ]

    if remaining:

        leverage_cluster = (
            leverage_score.loc[remaining]
            .idxmax()
        )

        names[leverage_cluster] = (
            "Value Cyclicals"
        )

    # ---------------------------------------------------------------
    # 4. Strong profitability + lower growth among remaining.
    # ---------------------------------------------------------------

    remaining = [
        c for c in profile.index
        if c not in names
    ]

    if remaining:

        defensive_cluster = (
            profitability_score.loc[remaining]
            .idxmax()
        )

        names[defensive_cluster] = (
            "Defensive Dividend Payers"
        )

    # ---------------------------------------------------------------
    # 5. Final remaining cluster.
    # ---------------------------------------------------------------

    remaining = [
        c for c in profile.index
        if c not in names
    ]

    if remaining:

        names[remaining[0]] = (
            "Distressed or Turnaround"
        )

    # Safety validation.
    if len(names) != N_CLUSTERS:
        raise ValueError(
            f"Expected {N_CLUSTERS} cluster names "
            f"but generated {len(names)}."
        )

    return names, profile


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def run_clustering():
    """Run the complete Day 36 clustering pipeline."""

    print("=" * 72)
    print(
        "SPRINT 6 — DAY 36 KMEANS FINANCIAL CLUSTERING"
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

    companies, sectors, ratios, growth = load_data()

    print(
        f"Official companies : {len(companies)}"
    )

    print(
        f"Ratio records      : {len(ratios)}"
    )

    print(
        f"Growth records     : {len(growth)}"
    )

    print("\nPreparing clustering features...")

    df = build_feature_dataset(
        companies,
        sectors,
        ratios,
        growth,
    )

    print(
        f"Companies prepared : {len(df)}"
    )

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 companies but found {len(df)}."
        )

    print("\nFeatures:")

    print(
        df[
            ["company_id", "broad_sector"] + FEATURES
        ]
        .head()
        .to_string(index=False)
    )

    # ---------------------------------------------------------------
    # Sector median imputation.
    # ---------------------------------------------------------------

    print(
        "\nApplying sector median imputation..."
    )

    df = impute_sector_medians(df)

    missing = (
        df[FEATURES]
        .isna()
        .sum()
        .sum()
    )

    if missing > 0:
        raise ValueError(
            f"{missing} missing feature values remain."
        )

    # ---------------------------------------------------------------
    # Scaling.
    # ---------------------------------------------------------------

    X = df[FEATURES].astype(float)

    print(
        "\nScaling features using StandardScaler..."
    )

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    print(
        "Features scaled successfully."
    )

    # ---------------------------------------------------------------
    # Elbow plot.
    # ---------------------------------------------------------------

    generate_elbow_plot(X_scaled)

    # ---------------------------------------------------------------
    # KMeans.
    # ---------------------------------------------------------------

    print("\nRunning KMeans...")

    kmeans = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=10,
    )

    cluster_ids = kmeans.fit_predict(
        X_scaled
    )

    df["cluster_id"] = cluster_ids

    # Distance from assigned centroid.
    distances = kmeans.transform(
        X_scaled
    )

    df["distance_from_centroid"] = [
        distances[i, cluster_ids[i]]
        for i in range(len(df))
    ]

    # ---------------------------------------------------------------
    # Cluster names.
    # ---------------------------------------------------------------

    cluster_names, profile = (
        assign_cluster_names(df)
    )

    df["cluster_name"] = (
        df["cluster_id"]
        .map(cluster_names)
    )

    # ---------------------------------------------------------------
    # Output.
    # ---------------------------------------------------------------

    df = (
        df.sort_values("company_id")
        .reset_index(drop=True)
    )

    output = df[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].copy()

    output["cluster_id"] = (
        output["cluster_id"]
        .astype(int)
    )

    output["distance_from_centroid"] = (
        output["distance_from_centroid"]
        .round(6)
    )

    output.to_csv(
        CLUSTER_OUTPUT,
        index=False,
    )

    # ---------------------------------------------------------------
    # SUMMARY.
    # ---------------------------------------------------------------

    print("\n" + "=" * 72)
    print(
        "DAY 36 CLUSTERING SUMMARY"
    )
    print("=" * 72)

    print(
        f"Companies clustered : {len(output)}"
    )

    print(
        f"Clusters            : "
        f"{output['cluster_id'].nunique()}"
    )

    print(
        f"Expected clusters   : {N_CLUSTERS}"
    )

    print("\nCluster distribution:")

    distribution = (
        output.groupby(
            ["cluster_id", "cluster_name"]
        )
        .size()
        .reset_index(name="companies")
        .sort_values("cluster_id")
    )

    print(
        distribution.to_string(
            index=False
        )
    )

    print("\nCluster names:")

    for cluster_id in sorted(
        cluster_names
    ):
        print(
            f"{cluster_id}: "
            f"{cluster_names[cluster_id]}"
        )

    print(
        f"\nOutput file : {CLUSTER_OUTPUT}"
    )

    print(
        f"Elbow plot  : {ELBOW_OUTPUT}"
    )

    # ---------------------------------------------------------------
    # VALIDATION.
    # ---------------------------------------------------------------

    if len(output) != 92:
        raise ValueError(
            "Cluster output does not contain "
            "all 92 companies."
        )

    if (
        output["company_id"]
        .nunique()
        != 92
    ):
        raise ValueError(
            "Duplicate or missing company IDs."
        )

    if (
        output["cluster_id"]
        .nunique()
        != 5
    ):
        raise ValueError(
            "KMeans did not produce exactly "
            "5 clusters."
        )

    if not (
        output["cluster_id"]
        .between(0, 4)
        .all()
    ):
        raise ValueError(
            "Cluster IDs must be between 0 and 4."
        )

    if (
        output["cluster_name"]
        .isna()
        .any()
    ):
        raise ValueError(
            "Some companies do not have "
            "a cluster name."
        )

    if not ELBOW_OUTPUT.exists():
        raise ValueError(
            "Elbow plot was not generated."
        )

    if not CLUSTER_OUTPUT.exists():
        raise ValueError(
            "Cluster labels CSV was not generated."
        )

    print("\nSTATUS: PASS")

    print(
        "All 92 companies assigned to "
        "5 reproducible KMeans clusters."
    )

    print("=" * 72)

    return output


if __name__ == "__main__":
    run_clustering()

