"""
Sprint 4 — Valuation Module

Calculates valuation metrics and valuation flags for the
official 92-company Nifty 100 universe.

Outputs:
    outputs/valuation_summary.xlsx
    outputs/valuation_flags.csv
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

DB_PATH = Path("data/nifty100.db")
OUTPUT_DIR = Path("outputs")

SUMMARY_OUTPUT = OUTPUT_DIR / "valuation_summary.xlsx"
FLAGS_OUTPUT = OUTPUT_DIR / "valuation_flags.csv"


# ------------------------------------------------------------------
# Database Helper
# ------------------------------------------------------------------

def get_connection():
    """Return a SQLite database connection."""

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    return sqlite3.connect(DB_PATH)


# ------------------------------------------------------------------
# Load Valuation Data
# ------------------------------------------------------------------

def load_valuation_data():
    """
    Load the official 92-company universe together with:

    - latest financial ratios
    - market valuation data
    - broad sector
    - five-year P/E history
    """

    conn = get_connection()

    try:

        query = """
            WITH latest_year AS (
                SELECT MAX(year) AS year
                FROM financial_ratios
            ),

            latest_ratios AS (
                SELECT
                    fr.company_id,
                    fr.year,
                    fr.free_cash_flow_cr
                FROM financial_ratios fr
                INNER JOIN latest_year ly
                    ON fr.year = ly.year
            ),

            latest_market AS (
                SELECT
                    mc.company_id,
                    mc.year,
                    mc.market_cap_crore,
                    mc.pe_ratio,
                    mc.pb_ratio,
                    mc.ev_ebitda
                FROM market_cap mc
                INNER JOIN latest_year ly
                    ON mc.year = ly.year
            ),

            latest_sector AS (
                SELECT
                    company_id,
                    broad_sector
                FROM sectors
            )

            SELECT
                c.id AS company_id,
                c.company_name,

                s.broad_sector AS sector,

                r.year,

                r.free_cash_flow_cr,

                m.market_cap_crore,
                m.pe_ratio,
                m.pb_ratio,
                m.ev_ebitda

            FROM companies c

            LEFT JOIN latest_ratios r
                ON c.id = r.company_id

            LEFT JOIN latest_market m
                ON c.id = m.company_id

            LEFT JOIN latest_sector s
                ON c.id = s.company_id

            ORDER BY
                c.company_name
        """

        latest_df = pd.read_sql_query(
            query,
            conn,
        )

        # ----------------------------------------------------------
        # Five-year P/E history
        # ----------------------------------------------------------

        pe_history_query = """
            SELECT
                mc.company_id,
                mc.year,
                mc.pe_ratio
            FROM market_cap mc
            INNER JOIN companies c
                ON mc.company_id = c.id
            WHERE
                mc.year BETWEEN
                    (
                        SELECT MAX(year) - 4
                        FROM market_cap
                    )
                    AND
                    (
                        SELECT MAX(year)
                        FROM market_cap
                    )
        """

        pe_history_df = pd.read_sql_query(
            pe_history_query,
            conn,
        )

    finally:
        conn.close()

    return latest_df, pe_history_df


# ------------------------------------------------------------------
# Five-Year Median P/E
# ------------------------------------------------------------------

def calculate_five_year_median_pe(pe_history_df):
    """
    Calculate the median P/E for each company across the
    latest five available market-cap years.

    Invalid or non-positive P/E values are excluded because
    they do not represent meaningful valuation multiples.
    """

    if pe_history_df.empty:
        return pd.DataFrame(
            columns=[
                "company_id",
                "5yr_median_PE",
            ]
        )

    df = pe_history_df.copy()

    df["pe_ratio"] = pd.to_numeric(
        df["pe_ratio"],
        errors="coerce",
    )

    # P/E <= 0 is not a meaningful conventional valuation multiple.
    df.loc[
        df["pe_ratio"] <= 0,
        "pe_ratio"
    ] = np.nan

    median_df = (
        df.groupby("company_id")["pe_ratio"]
        .median()
        .reset_index()
        .rename(
            columns={
                "pe_ratio": "5yr_median_PE"
            }
        )
    )

    return median_df


# ------------------------------------------------------------------
# FCF Yield
# ------------------------------------------------------------------

def calculate_fcf_yield(df):
    """
    Calculate FCF yield:

        FCF Yield = FCF / Market Cap × 100

    If FCF or market cap is unavailable, the result is NaN.

    Market cap must be positive.
    """

    result = df.copy()

    result["free_cash_flow_cr"] = pd.to_numeric(
        result["free_cash_flow_cr"],
        errors="coerce",
    )

    result["market_cap_crore"] = pd.to_numeric(
        result["market_cap_crore"],
        errors="coerce",
    )

    valid_market_cap = (
        result["market_cap_crore"] > 0
    )

    result["fcf_yield_pct"] = np.where(
        valid_market_cap,
        (
            result["free_cash_flow_cr"]
            / result["market_cap_crore"]
        ) * 100,
        np.nan,
    )

    return result


# ------------------------------------------------------------------
# Sector Median P/E
# ------------------------------------------------------------------

def calculate_sector_median_pe(df):
    """
    Calculate the latest-year median P/E for every sector.

    Non-positive P/E values are excluded.
    """

    sector_df = df.copy()

    sector_df["pe_ratio"] = pd.to_numeric(
        sector_df["pe_ratio"],
        errors="coerce",
    )

    sector_df.loc[
        sector_df["pe_ratio"] <= 0,
        "pe_ratio"
    ] = np.nan

    sector_medians = (
        sector_df
        .dropna(subset=["sector"])
        .groupby("sector")["pe_ratio"]
        .median()
        .reset_index()
        .rename(
            columns={
                "pe_ratio": "sector_median_pe"
            }
        )
    )

    return sector_medians


# ------------------------------------------------------------------
# Valuation Flags
# ------------------------------------------------------------------

def apply_valuation_flags(df):
    """
    Apply Sprint 4 valuation classification.

    P/E > sector median × 1.5
        -> Caution

    P/E < sector median × 0.7
        -> Discount

    Otherwise
        -> Fair

    If either P/E or sector median P/E is unavailable,
    classification is N/A.
    """

    result = df.copy()

    result["flag"] = "N/A"

    valid = (
        result["pe_ratio"].notna()
        & result["sector_median_pe"].notna()
        & (result["sector_median_pe"] > 0)
    )

    caution = (
        valid
        & (
            result["pe_ratio"]
            > result["sector_median_pe"] * 1.5
        )
    )

    discount = (
        valid
        & (
            result["pe_ratio"]
            < result["sector_median_pe"] * 0.7
        )
    )

    fair = valid & ~caution & ~discount

    result.loc[
        caution,
        "flag"
    ] = "Caution"

    result.loc[
        discount,
        "flag"
    ] = "Discount"

    result.loc[
        fair,
        "flag"
    ] = "Fair"

    # --------------------------------------------------------------
    # P/E vs sector median
    #
    # Example:
    # Sector median = 20
    # Company P/E = 30
    #
    # Difference = +50%
    # --------------------------------------------------------------

    result["PE_vs_sector_median_pct"] = np.where(
        valid,
        (
            (
                result["pe_ratio"]
                - result["sector_median_pe"]
            )
            / result["sector_median_pe"]
        ) * 100,
        np.nan,
    )

    return result


# ------------------------------------------------------------------
# Build Final Valuation Dataset
# ------------------------------------------------------------------

def build_valuation_dataset():
    """
    Build the complete valuation dataset for all 92 companies.
    """

    latest_df, pe_history_df = load_valuation_data()

    # --------------------------------------------------------------
    # FCF Yield
    # --------------------------------------------------------------

    valuation_df = calculate_fcf_yield(
        latest_df
    )

    # --------------------------------------------------------------
    # Five-Year Median P/E
    # --------------------------------------------------------------

    median_pe_df = (
        calculate_five_year_median_pe(
            pe_history_df
        )
    )

    valuation_df = valuation_df.merge(
        median_pe_df,
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------------
    # Sector Median P/E
    # --------------------------------------------------------------

    sector_medians = calculate_sector_median_pe(
        valuation_df
    )

    valuation_df = valuation_df.merge(
        sector_medians,
        on="sector",
        how="left",
    )

    # --------------------------------------------------------------
    # Flags
    # --------------------------------------------------------------

    valuation_df = apply_valuation_flags(
        valuation_df
    )

    return valuation_df


# ------------------------------------------------------------------
# Format Output
# ------------------------------------------------------------------

def format_output(df):
    """
    Select and format the official Sprint 4 output columns.
    """

    output = df.copy()

    output = output.rename(
        columns={
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        }
    )

    required_columns = [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "fcf_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]

    for column in required_columns:

        if column not in output.columns:
            output[column] = np.nan

    output = output[
        required_columns
    ]

    numeric_columns = [
        "P/E",
        "P/B",
        "EV/EBITDA",
        "fcf_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
    ]

    for column in numeric_columns:

        output[column] = pd.to_numeric(
            output[column],
            errors="coerce",
        ).round(2)

    return output


# ------------------------------------------------------------------
# Save Outputs
# ------------------------------------------------------------------

def save_outputs(df):
    """
    Save valuation summary and valuation flags.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------------
    # Complete 92-company summary
    # --------------------------------------------------------------

    df.to_excel(
        SUMMARY_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------------
    # Caution + Discount only
    # --------------------------------------------------------------

    flags_df = df[
        df["flag"].isin(
            ["Caution", "Discount"]
        )
    ].copy()

    flags_df.to_csv(
        FLAGS_OUTPUT,
        index=False,
    )

    return flags_df


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------

def validate_outputs(summary_df, flags_df):
    """
    Validate Sprint 4 valuation deliverables.
    """

    print()
    print("=" * 70)
    print("VALUATION MODULE VALIDATION")
    print("=" * 70)

    print(
        f"Companies in valuation summary: "
        f"{len(summary_df)}"
    )

    print(
        f"Unique companies: "
        f"{summary_df['company_id'].nunique()}"
    )

    print(
        f"Flagged companies: "
        f"{len(flags_df)}"
    )

    print()
    print("Flag distribution:")
    print(
        summary_df["flag"]
        .value_counts(dropna=False)
    )

    print()

    expected_columns = [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "fcf_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]

    missing_columns = [
        column
        for column in expected_columns
        if column not in summary_df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    if len(summary_df) != 92:
        raise ValueError(
            f"Expected 92 companies, "
            f"found {len(summary_df)}."
        )

    if summary_df["company_id"].nunique() != 92:
        raise ValueError(
            "Company IDs are not unique."
        )

    invalid_flags = set(
        summary_df["flag"].dropna().unique()
    ) - {
        "Caution",
        "Discount",
        "Fair",
        "N/A",
    }

    if invalid_flags:
        raise ValueError(
            "Unexpected valuation flags: "
            + ", ".join(sorted(invalid_flags))
        )

    print()
    print("Required columns: PASS")
    print("92-company universe: PASS")
    print("Unique company IDs: PASS")
    print("Valuation flags: PASS")

    print()
    print("Output files:")
    print(f"  {SUMMARY_OUTPUT}")
    print(f"  {FLAGS_OUTPUT}")

    print("=" * 70)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    """Run the complete valuation pipeline."""

    print()
    print("=" * 70)
    print("SPRINT 4 — VALUATION MODULE")
    print("=" * 70)

    valuation_df = build_valuation_dataset()

    output_df = format_output(
        valuation_df
    )

    flags_df = save_outputs(
        output_df
    )

    validate_outputs(
        output_df,
        flags_df,
    )

    print()
    print("Valuation module completed successfully.")
    print()


if __name__ == "__main__":
    main()