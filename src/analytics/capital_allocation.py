"""
Sprint 5 Day 32 - Capital Allocation Analysis

Validates and analyzes capital allocation patterns for the official
92-company universe.

Patterns:
    1. Reinvestor
    2. Liquidating Assets
    3. Distress Signal
    4. Growth Funded by Debt
    5. Cash Accumulator
    6. Pre-Revenue
    7. Mixed
    8. Unknown

Outputs:
    outputs/capital_allocation_distribution.csv
    outputs/pattern_changes.csv

Important:
    The companies table is the official 92-company universe.
    Supporting cash-flow records are filtered to that universe.

The capital allocation logic is intentionally consistent with the
capital_allocation_pattern() function used in cashflow_kpis.py.
"""

from pathlib import Path
import sqlite3

import pandas as pd


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

DB_PATH = Path("data/nifty100.db")

OUTPUT_DIR = Path("outputs")

DISTRIBUTION_FILE = (
    OUTPUT_DIR / "capital_allocation_distribution.csv"
)

PATTERN_CHANGES_FILE = (
    OUTPUT_DIR / "pattern_changes.csv"
)

EXPECTED_COMPANIES = 92


# ------------------------------------------------------------------
# Capital allocation classification
# ------------------------------------------------------------------

def capital_allocation_pattern(
    operating_activity,
    investing_activity,
    financing_activity,
):
    """
    Classify a company's capital allocation pattern.

    The logic matches the classification used in
    cashflow_kpis.py.
    """

    if (
        pd.isna(operating_activity)
        or pd.isna(investing_activity)
        or pd.isna(financing_activity)
    ):
        return "Unknown"

    cfo_positive = operating_activity > 0
    cfi_positive = investing_activity > 0
    cff_positive = financing_activity > 0

    # CFO positive, CFI negative, CFF negative
    if (
        cfo_positive
        and not cfi_positive
        and not cff_positive
    ):
        return "Reinvestor"

    # CFO positive, CFI positive, CFF negative
    if (
        cfo_positive
        and cfi_positive
        and not cff_positive
    ):
        return "Liquidating Assets"

    # CFO negative, CFI positive, CFF positive
    if (
        not cfo_positive
        and cfi_positive
        and cff_positive
    ):
        return "Distress Signal"

    # CFO negative, CFI negative, CFF positive
    if (
        not cfo_positive
        and not cfi_positive
        and cff_positive
    ):
        return "Growth Funded by Debt"

    # CFO positive, CFI positive, CFF positive
    if (
        cfo_positive
        and cfi_positive
        and cff_positive
    ):
        return "Cash Accumulator"

    # CFO negative, CFI negative, CFF negative
    if (
        not cfo_positive
        and not cfi_positive
        and not cff_positive
    ):
        return "Pre-Revenue"

    # CFO positive, CFI negative, CFF positive
    if (
        cfo_positive
        and not cfi_positive
        and cff_positive
    ):
        return "Mixed"

    return "Unknown"


# ------------------------------------------------------------------
# Database loading
# ------------------------------------------------------------------

def load_data():
    """
    Load the official companies, cash-flow data, and sectors.

    The companies table is the authoritative 92-company universe.

    Any supporting cash-flow records whose company_id is not present
    in companies are excluded from the Day 32 analysis.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)

    try:

        # ----------------------------------------------------------
        # Official company universe
        # ----------------------------------------------------------

        companies = pd.read_sql_query(
            """
            SELECT
                id AS company_id,
                company_name
            FROM companies
            ORDER BY id
            """,
            connection,
        )

        # ----------------------------------------------------------
        # Cash-flow data
        # ----------------------------------------------------------

        cashflow = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
            """,
            connection,
        )

        # ----------------------------------------------------------
        # Sector data
        # ----------------------------------------------------------

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector
            FROM sectors
            """,
            connection,
        )

    finally:
        connection.close()

    return companies, cashflow, sectors


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------

def validate_company_universe(companies):
    """
    Validate that the companies table contains exactly
    the official 92-company universe.
    """

    company_count = (
        companies["company_id"]
        .nunique()
    )

    if (
        len(companies) != EXPECTED_COMPANIES
        or company_count != EXPECTED_COMPANIES
    ):
        raise ValueError(
            "Official companies table must contain exactly "
            f"{EXPECTED_COMPANIES} unique companies. "
            f"Found {len(companies)} rows and "
            f"{company_count} unique IDs."
        )


def validate_cashflow_coverage(
    companies,
    cashflow,
):
    """
    Validate cash-flow coverage against the official company
    universe.

    Supporting cash-flow records outside the official universe
    are ignored rather than treated as an error.

    Returns
    -------
    tuple
        filtered_cashflow, coverage, excluded_company_ids
    """

    official_ids = set(
        companies["company_id"]
        .dropna()
        .unique()
    )

    cashflow_ids = set(
        cashflow["company_id"]
        .dropna()
        .unique()
    )

    # --------------------------------------------------------------
    # Identify supporting records outside official universe
    # --------------------------------------------------------------

    outside_universe = (
        cashflow_ids - official_ids
    )

    # --------------------------------------------------------------
    # Keep only the official 92 companies
    # --------------------------------------------------------------

    filtered_cashflow = cashflow[
        cashflow["company_id"].isin(
            official_ids
        )
    ].copy()

    # --------------------------------------------------------------
    # Calculate year coverage
    # --------------------------------------------------------------

    coverage = (
        filtered_cashflow
        .groupby("company_id")["year"]
        .agg(
            years_available="count",
            first_year="min",
            latest_year="max",
        )
        .reset_index()
    )

    coverage = companies[
        ["company_id"]
    ].merge(
        coverage,
        on="company_id",
        how="left",
    )

    coverage["years_available"] = (
        coverage["years_available"]
        .fillna(0)
        .astype(int)
    )

    return (
        filtered_cashflow,
        coverage,
        sorted(outside_universe),
    )


# ------------------------------------------------------------------
# Pattern calculation
# ------------------------------------------------------------------

def calculate_patterns(cashflow):
    """
    Calculate capital allocation pattern for every
    company-year observation.
    """

    result = cashflow.copy()

    # --------------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------------

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce",
    )

    numeric_columns = [
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ]

    for column in numeric_columns:

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    # --------------------------------------------------------------
    # Remove invalid company/year records
    # --------------------------------------------------------------

    result = result.dropna(
        subset=[
            "company_id",
            "year",
        ]
    )

    result["year"] = (
        result["year"]
        .astype(int)
    )

    # --------------------------------------------------------------
    # Apply capital allocation classification
    # --------------------------------------------------------------

    result["capital_allocation_label"] = (
        result.apply(
            lambda row:
                capital_allocation_pattern(
                    row["operating_activity"],
                    row["investing_activity"],
                    row["financing_activity"],
                ),
            axis=1,
        )
    )

    return (
        result
        .sort_values(
            [
                "company_id",
                "year",
            ]
        )
        .reset_index(drop=True)
    )


# ------------------------------------------------------------------
# Latest-year distribution
# ------------------------------------------------------------------

def latest_year_distribution(
    pattern_data,
):
    """
    Generate pattern distribution for the latest available
    year for each company.
    """

    latest = (
        pattern_data
        .sort_values(
            [
                "company_id",
                "year",
            ]
        )
        .drop_duplicates(
            "company_id",
            keep="last",
        )
        .copy()
    )

    distribution = (
        latest[
            "capital_allocation_label"
        ]
        .value_counts()
        .rename_axis(
            "capital_allocation_label"
        )
        .reset_index(
            name="company_count"
        )
    )

    # --------------------------------------------------------------
    # Ensure all 8 patterns are represented
    # --------------------------------------------------------------

    expected_patterns = [
        "Reinvestor",
        "Liquidating Assets",
        "Distress Signal",
        "Growth Funded by Debt",
        "Cash Accumulator",
        "Pre-Revenue",
        "Mixed",
        "Unknown",
    ]

    distribution = (
        pd.DataFrame(
            {
                "capital_allocation_label":
                    expected_patterns
            }
        )
        .merge(
            distribution,
            on="capital_allocation_label",
            how="left",
        )
    )

    distribution["company_count"] = (
        distribution["company_count"]
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------------------
    # Percentage of official companies
    # --------------------------------------------------------------

    if len(latest) > 0:

        distribution["percentage"] = (
            distribution["company_count"]
            / len(latest)
            * 100
        ).round(2)

    else:

        distribution["percentage"] = 0.0

    return latest, distribution


# ------------------------------------------------------------------
# Year-over-year pattern changes
# ------------------------------------------------------------------

def detect_pattern_changes(
    pattern_data,
):
    """
    Detect companies whose capital allocation pattern changed
    from one financial year to the next.

    Only actual pattern changes are included.
    """

    data = pattern_data.copy()

    data = data.sort_values(
        [
            "company_id",
            "year",
        ]
    )

    # --------------------------------------------------------------
    # Previous year
    # --------------------------------------------------------------

    data["previous_year"] = (
        data.groupby("company_id")[
            "year"
        ].shift(1)
    )

    # --------------------------------------------------------------
    # Previous pattern
    # --------------------------------------------------------------

    data["previous_pattern"] = (
        data.groupby("company_id")[
            "capital_allocation_label"
        ].shift(1)
    )

    # --------------------------------------------------------------
    # Keep only actual changes
    # --------------------------------------------------------------

    changes = data[
        data["previous_pattern"].notna()
        & (
            data["capital_allocation_label"]
            != data["previous_pattern"]
        )
    ].copy()

    if changes.empty:

        return pd.DataFrame(
            columns=[
                "company_id",
                "previous_year",
                "current_year",
                "previous_pattern",
                "current_pattern",
                "pattern_change",
            ]
        )

    changes["previous_year"] = (
        changes["previous_year"]
        .astype(int)
    )

    changes["year"] = (
        changes["year"]
        .astype(int)
    )

    changes = changes.rename(
        columns={
            "year": "current_year",
            "capital_allocation_label":
                "current_pattern",
        }
    )

    changes["pattern_change"] = (
        changes["previous_pattern"]
        + " -> "
        + changes["current_pattern"]
    )

    return changes[
        [
            "company_id",
            "previous_year",
            "current_year",
            "previous_pattern",
            "current_pattern",
            "pattern_change",
        ]
    ].reset_index(drop=True)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def generate():
    """
    Execute the complete Day 32 capital allocation analysis.
    """

    companies, cashflow, sectors = (
        load_data()
    )

    # --------------------------------------------------------------
    # Validate official universe
    # --------------------------------------------------------------

    validate_company_universe(
        companies
    )

    # --------------------------------------------------------------
    # Validate and filter cash-flow coverage
    # --------------------------------------------------------------

    (
        cashflow,
        coverage,
        excluded_company_ids,
    ) = validate_cashflow_coverage(
        companies,
        cashflow,
    )

    # --------------------------------------------------------------
    # Calculate patterns
    # --------------------------------------------------------------

    pattern_data = calculate_patterns(
        cashflow
    )

    # --------------------------------------------------------------
    # Add sector information
    # --------------------------------------------------------------

    sector_data = (
        sectors[
            [
                "company_id",
                "broad_sector",
            ]
        ]
        .drop_duplicates(
            "company_id"
        )
    )

    pattern_data = pattern_data.merge(
        sector_data,
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------------
    # Latest-year distribution
    # --------------------------------------------------------------

    latest, distribution = (
        latest_year_distribution(
            pattern_data
        )
    )

    # --------------------------------------------------------------
    # Pattern changes
    # --------------------------------------------------------------

    pattern_changes = (
        detect_pattern_changes(
            pattern_data
        )
    )

    # --------------------------------------------------------------
    # Output directory
    # --------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------------
    # Save distribution
    # --------------------------------------------------------------

    distribution.to_csv(
        DISTRIBUTION_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # Save pattern changes
    # --------------------------------------------------------------

    pattern_changes.to_csv(
        PATTERN_CHANGES_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # Validation statistics
    # --------------------------------------------------------------

    latest_company_count = (
        latest["company_id"]
        .nunique()
    )

    companies_with_cashflow = int(
        (
            coverage["years_available"]
            > 0
        ).sum()
    )

    total_company_years = len(
        pattern_data
    )

    changed_companies = (
        pattern_changes[
            "company_id"
        ].nunique()
        if not pattern_changes.empty
        else 0
    )

    # --------------------------------------------------------------
    # Coverage warnings
    # --------------------------------------------------------------

    missing_cashflow = coverage.loc[
        coverage["years_available"] == 0,
        "company_id",
    ].tolist()

    # --------------------------------------------------------------
    # Console report
    # --------------------------------------------------------------

    print("=" * 72)

    print(
        "SPRINT 5 — DAY 32 "
        "CAPITAL ALLOCATION ANALYSIS"
    )

    print("=" * 72)

    print(
        f"Official companies      : "
        f"{len(companies)}"
    )

    print(
        f"Companies with cashflow : "
        f"{companies_with_cashflow}/"
        f"{EXPECTED_COMPANIES}"
    )

    print(
        f"Company-year records    : "
        f"{total_company_years}"
    )

    print(
        f"Latest-year companies   : "
        f"{latest_company_count}/"
        f"{EXPECTED_COMPANIES}"
    )

    print(
        f"Pattern changes         : "
        f"{len(pattern_changes)}"
    )

    print(
        f"Companies with changes  : "
        f"{changed_companies}"
    )

    print(
        f"Distribution output     : "
        f"{DISTRIBUTION_FILE}"
    )

    print(
        f"Pattern changes output  : "
        f"{PATTERN_CHANGES_FILE}"
    )

    # --------------------------------------------------------------
    # Extra supporting records
    # --------------------------------------------------------------

    if excluded_company_ids:

        print()
        print(
            "Supporting cash-flow records "
            "excluded from official universe:"
        )

        print(
            ", ".join(
                excluded_company_ids
            )
        )

        print(
            f"Excluded company IDs     : "
            f"{len(excluded_company_ids)}"
        )

    # --------------------------------------------------------------
    # Latest distribution
    # --------------------------------------------------------------

    print()
    print(
        "Latest-year capital allocation distribution:"
    )

    print(
        distribution.to_string(
            index=False
        )
    )

    # --------------------------------------------------------------
    # Missing cash-flow coverage
    # --------------------------------------------------------------

    if missing_cashflow:

        print()
        print(
            "WARNING — Companies with no "
            "cash-flow records:"
        )

        print(
            ", ".join(
                missing_cashflow
            )
        )

    # --------------------------------------------------------------
    # Final validation
    # --------------------------------------------------------------

    print()

    if (
        latest_company_count
        == EXPECTED_COMPANIES
        and companies_with_cashflow
        == EXPECTED_COMPANIES
    ):

        print(
            "DAY 32 STATUS: PASS"
        )

    else:

        print(
            "DAY 32 STATUS: REVIEW"
        )

    print("=" * 72)

    return (
        pattern_data,
        distribution,
        pattern_changes,
    )


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    generate()