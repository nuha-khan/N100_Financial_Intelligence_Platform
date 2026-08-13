import re
from pathlib import Path

import pandas as pd
import sqlite3


# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------

INPUT_FILE = Path("data/raw/analysis.xlsx")
OUTPUT_DIR = Path("outputs")

PARSED_OUTPUT = OUTPUT_DIR / "analysis_parsed.csv"
FAILURE_OUTPUT = OUTPUT_DIR / "parse_failures.csv"

DB_FILE = Path("data/nifty100.db")
CAGR_VALIDATION_OUTPUT = OUTPUT_DIR / "cagr_validation.csv"

# ------------------------------------------------------------------
# Target Metrics
# ------------------------------------------------------------------

TARGET_COLUMNS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


# ------------------------------------------------------------------
# Regex Patterns
# ------------------------------------------------------------------

# Examples handled:
# 10 Years: 21%
# 5 Years: 24%
# 3 Years: -1%
# 1 Year: -2%
#
# The pattern also allows inconsistent spaces around the colon.

YEAR_PATTERN = re.compile(
    r"(\d+)\s*Years?\s*:?\s*(-?[\d.]+)\s*%"
)

# Examples:
# TTM: 43%
# Last Year: 12%

SPECIAL_PERIOD_PATTERN = re.compile(
    r"(TTM|Last\s+Year)\s*:?\s*(-?[\d.]+)\s*%",
    re.IGNORECASE,
)


# ------------------------------------------------------------------
# Period Conversion
# ------------------------------------------------------------------

def period_to_years(period):
    """
    Convert textual periods into a numeric representation.

    TTM and Last Year are treated as one-year periods.
    """

    period = period.strip().lower()

    if period == "ttm":
        return 1

    if period == "last year":
        return 1

    return None


# ------------------------------------------------------------------
# Value Parser
# ------------------------------------------------------------------

def parse_metric_value(value):
    """
    Parse one analysis metric text value.

    Returns:
        (period_years, value_pct)

    If the value cannot be parsed:
        returns (None, None)
    """

    if pd.isna(value):
        return None, None

    text = str(value).strip()

    # --------------------------------------------------------------
    # Standard year-based format
    # --------------------------------------------------------------

    match = YEAR_PATTERN.search(text)

    if match:
        period_years = int(match.group(1))
        value_pct = float(match.group(2))

        return period_years, value_pct

    # --------------------------------------------------------------
    # TTM / Last Year format
    # --------------------------------------------------------------

    match = SPECIAL_PERIOD_PATTERN.search(text)

    if match:
        period_years = period_to_years(match.group(1))
        value_pct = float(match.group(2))

        return period_years, value_pct

    return None, None


# ------------------------------------------------------------------
# Main Parser
# ------------------------------------------------------------------

def parse_analysis_file():
    """
    Parse analysis.xlsx into a normalized long-format CSV.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # The first row contains the Excel title.
    # Actual column headers begin on the second row.
    df = pd.read_excel(
        INPUT_FILE,
        skiprows=1,
    )

    parsed_rows = []
    failures = []

    for _, row in df.iterrows():

        company_id = row["company_id"]

        for metric_column in TARGET_COLUMNS:

            raw_value = row[metric_column]

            period_years, value_pct = parse_metric_value(
                raw_value
            )

            if period_years is None:
                failures.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_column,
                        "raw_value": raw_value,
                        "reason": "Unable to parse metric value",
                    }
                )

                continue

            parsed_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_column,
                    "period_years": period_years,
                    "value_pct": value_pct,
                }
            )

    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failures_df = pd.DataFrame(
        failures,
        columns=[
            "company_id",
            "metric_type",
            "raw_value",
            "reason",
        ],
    )

    parsed_df.to_csv(
        PARSED_OUTPUT,
        index=False,
    )

    failures_df.to_csv(
        FAILURE_OUTPUT,
        index=False,
    )

    return parsed_df, failures_df


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------

def validate_output(parsed_df, failures_df):
    """
    Print basic validation information.
    """

    print("=" * 70)
    print("SPRINT 5 — NLP ANALYSIS TEXT PARSER")
    print("=" * 70)

    print(f"\nInput file: {INPUT_FILE}")
    print(f"Companies parsed: {parsed_df['company_id'].nunique()}")
    print(f"Parsed records: {len(parsed_df)}")
    print(f"Parse failures: {len(failures_df)}")

    print("\nMetric distribution:")
    print(
        parsed_df["metric_type"]
        .value_counts()
        .sort_index()
    )

    print("\nPeriod distribution:")
    print(
        parsed_df["period_years"]
        .value_counts()
        .sort_index()
    )

    print("\nOutput files:")
    print(f"  {PARSED_OUTPUT}")
    print(f"  {FAILURE_OUTPUT}")

    print("\n" + "=" * 70)

# ------------------------------------------------------------------
# CAGR Cross Validation
# ------------------------------------------------------------------

def validate_cagr_against_ratio_engine(parsed_df):
    """
    Cross-validate 5-year CAGR values parsed from analysis.xlsx
    against the CAGR values calculated by the Ratio Engine.

    Only the following metrics are compared:

        compounded_sales_growth -> revenue_cagr_5y
        compounded_profit_growth -> pat_cagr_5y

    Divergence greater than 5% is flagged for manual review.
    """

    comparison_map = {
        "compounded_sales_growth": "revenue_cagr_5y",
        "compounded_profit_growth": "pat_cagr_5y",
    }

    # Only 5-year CAGR records are relevant for this validation.
    cagr_df = parsed_df[
        parsed_df["period_years"] == 5
    ].copy()

    if cagr_df.empty:
        print("\nNo 5-year CAGR records found for validation.")
        return pd.DataFrame()

    # --------------------------------------------------------------
    # Load computed CAGR values from SQLite
    # --------------------------------------------------------------

    con = sqlite3.connect(DB_FILE)

    ratio_df = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            revenue_cagr_5y,
            pat_cagr_5y
        FROM financial_ratios
        """,
        con,
    )

    con.close()

    # --------------------------------------------------------------
    # Keep latest available year for each company
    # --------------------------------------------------------------

    ratio_df = (
        ratio_df
        .sort_values("year")
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    validation_rows = []

    # --------------------------------------------------------------
    # Compare parsed values against Ratio Engine values
    # --------------------------------------------------------------

    for _, row in cagr_df.iterrows():

        metric_type = row["metric_type"]

        if metric_type not in comparison_map:
            continue

        ratio_column = comparison_map[metric_type]

        company_id = row["company_id"]
        parsed_value = row["value_pct"]

        match = ratio_df[
            ratio_df["company_id"] == company_id
        ]

        if match.empty:
            validation_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "parsed_value_pct": parsed_value,
                    "computed_value_pct": None,
                    "divergence_pct": None,
                    "status": "REVIEW",
                    "reason": "Company not found in Ratio Engine",
                }
            )
            continue

        computed_value = match.iloc[0][ratio_column]

        if pd.isna(computed_value):
            validation_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "parsed_value_pct": parsed_value,
                    "computed_value_pct": None,
                    "divergence_pct": None,
                    "status": "REVIEW",
                    "reason": "Computed CAGR unavailable",
                }
            )
            continue

        computed_value = float(computed_value)

        # Avoid division by zero.
        if computed_value == 0:
            divergence = (
                0.0
                if parsed_value == 0
                else None
            )
        else:
            divergence = (
                abs(parsed_value - computed_value)
                / abs(computed_value)
            ) * 100

        if divergence is None:
            status = "REVIEW"
            reason = "Unable to calculate divergence"
        elif divergence > 5:
            status = "REVIEW"
            reason = "Divergence exceeds 5%"
        else:
            status = "PASS"
            reason = "Within 5% tolerance"

        validation_rows.append(
            {
                "company_id": company_id,
                "metric_type": metric_type,
                "parsed_value_pct": parsed_value,
                "computed_value_pct": computed_value,
                "divergence_pct": round(divergence, 2)
                if divergence is not None
                else None,
                "status": status,
                "reason": reason,
            }
        )

    validation_df = pd.DataFrame(
        validation_rows,
        columns=[
            "company_id",
            "metric_type",
            "parsed_value_pct",
            "computed_value_pct",
            "divergence_pct",
            "status",
            "reason",
        ],
    )

    validation_df.to_csv(
        CAGR_VALIDATION_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------------
    # Validation Summary
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("CAGR CROSS-VALIDATION")
    print("=" * 70)

    print(
        f"\nRecords compared: {len(validation_df)}"
    )

    if not validation_df.empty:
        print("\nValidation status:")
        print(
            validation_df["status"]
            .value_counts()
        )

        review_df = validation_df[
            validation_df["status"] == "REVIEW"
        ]

        if not review_df.empty:
            print(
                "\n⚠️ Records requiring manual review:"
            )
            print(
                review_df.to_string(index=False)
            )
        else:
            print(
                "\nAll parsed 5-year CAGR values "
                "are within the 5% tolerance."
            )

    print(
        f"\nValidation output:"
        f"\n  {CAGR_VALIDATION_OUTPUT}"
    )

    print("=" * 70)

    return validation_df

# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------

if __name__ == "__main__":

    parsed, failures = parse_analysis_file()

    validate_output(
        parsed,
        failures,
    )

    validate_cagr_against_ratio_engine(
        parsed
    )