"""
Sprint 5 — Day 31
Cash Flow Intelligence Module

Generates company-level cash flow intelligence for all 92 official
companies in the Nifty 100 Financial Intelligence Platform.

Outputs
-------
output/cashflow_intelligence.xlsx
output/distress_alerts.csv

Required intelligence:
    - CFO Quality Score
    - CFO Quality Label
    - CapEx Intensity
    - CapEx Label
    - FCF CAGR (5Y)
    - FCF Conversion Rate
    - Distress Signal
    - Deleveraging Flag
    - Capital Allocation Pattern
"""

from pathlib import Path
import sqlite3

import pandas as pd


# ==================================================================
# CONFIGURATION
# ==================================================================

DB_PATH = Path("data/nifty100.db")

OUTPUT_DIR = Path("outputs")

INTELLIGENCE_FILE = (
    OUTPUT_DIR / "cashflow_intelligence.xlsx"
)

DISTRESS_FILE = (
    OUTPUT_DIR / "distress_alerts.csv"
)

EXPECTED_COMPANIES = 92


# ==================================================================
# UTILITY FUNCTIONS
# ==================================================================

def clean_numeric(
    df: pd.DataFrame,
    columns: list,
) -> pd.DataFrame:
    """
    Convert selected columns to numeric.

    Invalid values are converted to NaN.
    """

    result = df.copy()

    for column in columns:

        if column in result.columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result


def company_history(
    df: pd.DataFrame,
    company_id: str,
) -> pd.DataFrame:
    """
    Return chronological records for one company.
    """

    if df.empty:
        return df.copy()

    result = df[
        df["company_id"] == company_id
    ].copy()

    if "year" in result.columns:

        result = result.sort_values(
            "year"
        )

    return result.reset_index(
        drop=True
    )


def latest_valid_row(
    df: pd.DataFrame,
) -> pd.Series:
    """
    Return the latest available row.

    Rows without a valid year are ignored when possible.
    """

    if df.empty:
        return pd.Series(dtype=float)

    result = df.copy()

    if "year" in result.columns:

        valid_year = result[
            result["year"].notna()
        ]

        if not valid_year.empty:

            return (
                valid_year
                .sort_values("year")
                .iloc[-1]
            )

    return result.iloc[-1]


# ==================================================================
# FREE CASH FLOW
# ==================================================================

def free_cash_flow(
    operating_activity,
    investing_activity,
):
    """
    Free Cash Flow (Cr)

    Formula:
        Operating Cash Flow + Investing Cash Flow
    """

    if (
        pd.isna(operating_activity)
        or pd.isna(investing_activity)
    ):
        return None

    return round(
        float(operating_activity)
        + float(investing_activity),
        2,
    )


# ==================================================================
# CAPEX INTENSITY
# ==================================================================

def capex_intensity(
    investing_activity,
    sales,
):
    """
    CapEx Intensity (%)

    Formula:
        |Investing Activity| / Sales × 100

    Labels:
        < 3%       Asset Light
        3–8%       Moderate
        > 8%       Capital Intensive
    """

    if (
        pd.isna(investing_activity)
        or pd.isna(sales)
        or sales == 0
    ):
        return None, None

    intensity = (
        abs(float(investing_activity))
        / float(sales)
    ) * 100

    if intensity < 3:

        label = "Asset Light"

    elif intensity <= 8:

        label = "Moderate"

    else:

        label = "Capital Intensive"

    return round(intensity, 2), label


# ==================================================================
# FCF CONVERSION
# ==================================================================

def fcf_conversion_rate(
    operating_activity,
    investing_activity,
    operating_profit,
):
    """
    FCF Conversion Rate (%)

    Formula:
        FCF / Operating Profit × 100
    """

    if (
        pd.isna(operating_profit)
        or operating_profit == 0
    ):
        return None

    fcf = free_cash_flow(
        operating_activity,
        investing_activity,
    )

    if fcf is None:
        return None

    return round(
        (
            fcf
            / float(operating_profit)
        ) * 100,
        2,
    )


# ==================================================================
# CAPITAL ALLOCATION PATTERN
# ==================================================================

def capital_allocation_pattern(
    operating_activity,
    investing_activity,
    financing_activity,
):
    """
    Classify the latest capital allocation pattern.

    The classification is based on the signs of:

        CFO = Operating Cash Flow
        CFI = Investing Cash Flow
        CFF = Financing Cash Flow

    Patterns:

        CFO +, CFI -, CFF - -> Reinvestor
        CFO +, CFI +, CFF - -> Liquidating Assets
        CFO -, CFI +, CFF + -> Distress Signal
        CFO -, CFI -, CFF + -> Growth Funded by Debt
        CFO +, CFI +, CFF + -> Cash Accumulator
        CFO -, CFI -, CFF - -> Pre-Revenue
        CFO +, CFI -, CFF + -> Mixed

    The remaining combination is retained as Unknown.
    """

    if (
        pd.isna(operating_activity)
        or pd.isna(investing_activity)
        or pd.isna(financing_activity)
    ):
        return "Unknown"

    cfo_positive = (
        float(operating_activity) > 0
    )

    cfi_positive = (
        float(investing_activity) > 0
    )

    cff_positive = (
        float(financing_activity) > 0
    )

    # CFO + / CFI - / CFF -
    if (
        cfo_positive
        and not cfi_positive
        and not cff_positive
    ):
        return "Reinvestor"

    # CFO + / CFI + / CFF -
    if (
        cfo_positive
        and cfi_positive
        and not cff_positive
    ):
        return "Liquidating Assets"

    # CFO - / CFI + / CFF +
    if (
        not cfo_positive
        and cfi_positive
        and cff_positive
    ):
        return "Distress Signal"

    # CFO - / CFI - / CFF +
    if (
        not cfo_positive
        and not cfi_positive
        and cff_positive
    ):
        return "Growth Funded by Debt"

    # CFO + / CFI + / CFF +
    if (
        cfo_positive
        and cfi_positive
        and cff_positive
    ):
        return "Cash Accumulator"

    # CFO - / CFI - / CFF -
    if (
        not cfo_positive
        and not cfi_positive
        and not cff_positive
    ):
        return "Pre-Revenue"

    # CFO + / CFI - / CFF +
    if (
        cfo_positive
        and not cfi_positive
        and cff_positive
    ):
        return "Mixed"

    return "Unknown"


# ==================================================================
# CFO QUALITY SCORE
# ==================================================================

def cfo_quality_score(
    company_df: pd.DataFrame,
):
    """
    Calculate CFO Quality Score.

    Formula:
        Average(CFO / Net Profit)

    over the latest 5 available financial years.

    Labels:
        > 1.0      High Quality
        0.5–1.0    Moderate
        < 0.5      Accrual Risk
    """

    if company_df.empty:

        return None, "INSUFFICIENT"

    df = company_df.copy()

    if "year" in df.columns:

        df = df.sort_values(
            "year"
        )

    if len(df) < 5:

        return None, "INSUFFICIENT"

    recent = df.tail(5)

    ratios = []

    for _, row in recent.iterrows():

        cfo = row.get(
            "operating_activity"
        )

        pat = row.get(
            "net_profit"
        )

        if (
            pd.isna(cfo)
            or pd.isna(pat)
            or pat == 0
        ):
            continue

        ratios.append(
            float(cfo) / float(pat)
        )

    if not ratios:

        return None, "INSUFFICIENT"

    score = sum(ratios) / len(ratios)

    if score > 1.0:

        label = "High Quality"

    elif score >= 0.5:

        label = "Moderate"

    else:

        label = "Accrual Risk"

    return round(score, 2), label


# ==================================================================
# FCF CAGR — 5 YEARS
# ==================================================================

def fcf_cagr_5yr(
    company_df: pd.DataFrame,
):
    """
    Calculate 5-year FCF CAGR.

    FCF:
        CFO + CFI

    The calculation requires:
        - at least 5 available observations
        - positive starting FCF
        - positive ending FCF

    Returns None when CAGR cannot be calculated reliably.
    """

    if company_df.empty:

        return None

    df = company_df.copy()

    if "year" in df.columns:

        df = df.sort_values(
            "year"
        )

    df["fcf"] = (
        pd.to_numeric(
            df["operating_activity"],
            errors="coerce",
        )
        +
        pd.to_numeric(
            df["investing_activity"],
            errors="coerce",
        )
    )

    df = df[
        df["fcf"].notna()
    ].copy()

    if len(df) < 5:

        return None

    recent = df.tail(5)

    start_fcf = float(
        recent.iloc[0]["fcf"]
    )

    end_fcf = float(
        recent.iloc[-1]["fcf"]
    )

    if (
        start_fcf <= 0
        or end_fcf <= 0
    ):
        return None

    if (
        "year" not in recent.columns
        or recent["year"].isna().any()
    ):
        return None

    start_year = float(
        recent.iloc[0]["year"]
    )

    end_year = float(
        recent.iloc[-1]["year"]
    )

    years = (
        end_year
        - start_year
    )

    if years <= 0:

        return None

    cagr = (
        (
            end_fcf
            / start_fcf
        )
        ** (1 / years)
        - 1
    ) * 100

    return round(
        cagr,
        2,
    )


# ==================================================================
# DISTRESS SIGNAL
# ==================================================================

def distress_signal(
    operating_activity,
    financing_activity,
):
    """
    Distress Signal condition:

        CFO < 0 AND CFF > 0

    Meaning:
        The company is burning cash from operations
        while raising cash through financing.
    """

    if (
        pd.isna(operating_activity)
        or pd.isna(financing_activity)
    ):
        return False

    return bool(
        float(operating_activity) < 0
        and float(financing_activity) > 0
    )


# ==================================================================
# DELEVERAGING FLAG
# ==================================================================

def deleveraging_flag(
    financing_activity,
    current_borrowings,
    previous_borrowings,
):
    """
    Deleveraging condition:

        CFF < 0
        AND current borrowings < previous borrowings
    """

    if (
        pd.isna(financing_activity)
        or pd.isna(current_borrowings)
        or pd.isna(previous_borrowings)
    ):
        return False

    return bool(
        float(financing_activity) < 0
        and float(current_borrowings)
        < float(previous_borrowings)
    )


# ==================================================================
# DATABASE LOADING
# ==================================================================

def load_data():
    """
    Load all tables required for Day 31.
    """

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )

    try:

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

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector,
                sub_sector
            FROM sectors
            """,
            connection,
        )

        cashflow = pd.read_sql_query(
            """
            SELECT *
            FROM cashflow
            """,
            connection,
        )

        pnl = pd.read_sql_query(
            """
            SELECT *
            FROM profitandloss
            """,
            connection,
        )

        balancesheet = pd.read_sql_query(
            """
            SELECT *
            FROM balancesheet
            """,
            connection,
        )

    finally:

        connection.close()

    # --------------------------------------------------------------
    # Validate official universe
    # --------------------------------------------------------------

    company_count = (
        companies["company_id"]
        .nunique()
    )

    if (
        len(companies)
        != EXPECTED_COMPANIES
        or company_count
        != EXPECTED_COMPANIES
    ):

        raise ValueError(
            "The companies table must contain "
            f"exactly {EXPECTED_COMPANIES} "
            "unique companies. "
            f"Found {len(companies)} rows "
            f"and {company_count} unique IDs."
        )

    official_ids = set(
        companies["company_id"]
    )

    # --------------------------------------------------------------
    # Restrict analytical tables
    # --------------------------------------------------------------

    sectors = sectors[
        sectors["company_id"].isin(
            official_ids
        )
    ].copy()

    cashflow = cashflow[
        cashflow["company_id"].isin(
            official_ids
        )
    ].copy()

    pnl = pnl[
        pnl["company_id"].isin(
            official_ids
        )
    ].copy()

    balancesheet = balancesheet[
        balancesheet["company_id"].isin(
            official_ids
        )
    ].copy()

    # --------------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------------

    cashflow = clean_numeric(
        cashflow,
        [
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
        ],
    )

    pnl = clean_numeric(
        pnl,
        [
            "year",
            "sales",
            "operating_profit",
            "net_profit",
        ],
    )

    balancesheet = clean_numeric(
        balancesheet,
        [
            "year",
            "borrowings",
        ],
    )

    return (
        companies,
        sectors,
        cashflow,
        pnl,
        balancesheet,
    )


# ==================================================================
# COMPANY INTELLIGENCE
# ==================================================================

def calculate_company_intelligence(
    company_id,
    sector,
    cashflow_history,
    pnl_history,
    balance_history,
):
    """
    Calculate all required Day 31 metrics for one company.
    """

    # --------------------------------------------------------------
    # Sort histories
    # --------------------------------------------------------------

    cashflow_history = (
        cashflow_history
        .sort_values("year")
        .copy()
    )

    pnl_history = (
        pnl_history
        .sort_values("year")
        .copy()
    )

    balance_history = (
        balance_history
        .sort_values("year")
        .copy()
    )

    # --------------------------------------------------------------
    # CFO Quality
    #
    # Merge cash flow with PAT using year.
    # --------------------------------------------------------------

    cfo_quality_df = pd.DataFrame()

    if (
        not cashflow_history.empty
        and not pnl_history.empty
    ):

        cfo_quality_df = pd.merge(
            cashflow_history[
                [
                    "year",
                    "operating_activity",
                ]
            ],
            pnl_history[
                [
                    "year",
                    "net_profit",
                ]
            ],
            on="year",
            how="inner",
        )

    score, quality_label = (
        cfo_quality_score(
            cfo_quality_df
        )
    )

    # --------------------------------------------------------------
    # FCF CAGR
    # --------------------------------------------------------------

    fcf_growth = (
        fcf_cagr_5yr(
            cashflow_history
        )
    )

    # --------------------------------------------------------------
    # Latest cash flow
    # --------------------------------------------------------------

    latest_cashflow = (
        latest_valid_row(
            cashflow_history
        )
    )

    if latest_cashflow.empty:

        latest_cfo = None
        latest_cfi = None
        latest_cff = None

    else:

        latest_cfo = latest_cashflow.get(
            "operating_activity"
        )

        latest_cfi = latest_cashflow.get(
            "investing_activity"
        )

        latest_cff = latest_cashflow.get(
            "financing_activity"
        )

    # --------------------------------------------------------------
    # Latest P&L
    # --------------------------------------------------------------

    latest_pnl = (
        latest_valid_row(
            pnl_history
        )
    )

    if latest_pnl.empty:

        latest_sales = None
        latest_operating_profit = None
        latest_pat = None

    else:

        latest_sales = latest_pnl.get(
            "sales"
        )

        latest_operating_profit = (
            latest_pnl.get(
                "operating_profit"
            )
        )

        latest_pat = latest_pnl.get(
            "net_profit"
        )

    # --------------------------------------------------------------
    # CapEx Intensity
    # --------------------------------------------------------------

    capex_pct, capex_label = (
        capex_intensity(
            latest_cfi,
            latest_sales,
        )
    )

    # --------------------------------------------------------------
    # FCF Conversion
    # --------------------------------------------------------------

    fcf_conversion = (
        fcf_conversion_rate(
            latest_cfo,
            latest_cfi,
            latest_operating_profit,
        )
    )

    # --------------------------------------------------------------
    # Distress Flag
    # --------------------------------------------------------------

    distress = distress_signal(
        latest_cfo,
        latest_cff,
    )

    # --------------------------------------------------------------
    # Deleveraging Flag
    # --------------------------------------------------------------

    previous_borrowings = None
    current_borrowings = None

    if not balance_history.empty:

        balance_valid = (
            balance_history[
                [
                    "year",
                    "borrowings",
                ]
            ]
            .dropna(
                subset=["year"]
            )
            .sort_values("year")
        )

        if len(balance_valid) >= 1:

            current_borrowings = (
                balance_valid.iloc[-1][
                    "borrowings"
                ]
            )

        if len(balance_valid) >= 2:

            previous_borrowings = (
                balance_valid.iloc[-2][
                    "borrowings"
                ]
            )

    deleveraging = (
        deleveraging_flag(
            latest_cff,
            current_borrowings,
            previous_borrowings,
        )
    )

    # --------------------------------------------------------------
    # Capital Allocation Pattern
    # --------------------------------------------------------------

    capital_pattern = (
        capital_allocation_pattern(
            latest_cfo,
            latest_cfi,
            latest_cff,
        )
    )

    return {
        "company_id": company_id,
        "sector": sector,
        "cfo_quality_score": score,
        "cfo_quality_label": quality_label,
        "capex_intensity_pct": capex_pct,
        "capex_label": capex_label,
        "fcf_cagr_5yr": fcf_growth,
        "fcf_conversion_pct": fcf_conversion,
        "distress_flag": bool(distress),
        "deleveraging_flag": bool(deleveraging),
        "capital_allocation_label": capital_pattern,
        "_latest_cfo": latest_cfo,
        "_latest_cff": latest_cff,
        "_latest_net_profit": latest_pat,
    }


# ==================================================================
# GENERATE INTELLIGENCE
# ==================================================================

def generate():
    """
    Generate Day 31 Cash Flow Intelligence outputs.
    """

    (
        companies,
        sectors,
        cashflow,
        pnl,
        balancesheet,
    ) = load_data()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    # --------------------------------------------------------------
    # Generate one row per official company
    # --------------------------------------------------------------

    for company_id in companies[
        "company_id"
    ]:

        company_row = companies[
            companies["company_id"]
            == company_id
        ]

        company_sector = ""

        sector_rows = sectors[
            sectors["company_id"]
            == company_id
        ]

        if not sector_rows.empty:

            company_sector = str(
                sector_rows.iloc[0].get(
                    "broad_sector",
                    "",
                )
            )

        cashflow_history = (
            company_history(
                cashflow,
                company_id,
            )
        )

        pnl_history = (
            company_history(
                pnl,
                company_id,
            )
        )

        balance_history = (
            company_history(
                balancesheet,
                company_id,
            )
        )

        intelligence = (
            calculate_company_intelligence(
                company_id=company_id,
                sector=company_sector,
                cashflow_history=(
                    cashflow_history
                ),
                pnl_history=(
                    pnl_history
                ),
                balance_history=(
                    balance_history
                ),
            )
        )

        results.append(
            intelligence
        )

    result = pd.DataFrame(
        results
    )

    # --------------------------------------------------------------
    # Required final columns
    # --------------------------------------------------------------

    output_columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]

    output = result[
        output_columns
    ].copy()

    # --------------------------------------------------------------
    # Ensure exactly 92 companies
    # --------------------------------------------------------------

    if (
        len(output)
        != EXPECTED_COMPANIES
    ):

        raise ValueError(
            "Cash flow intelligence must "
            f"contain exactly {EXPECTED_COMPANIES} "
            f"rows. Generated {len(output)}."
        )

    if (
        output["company_id"]
        .nunique()
        != EXPECTED_COMPANIES
    ):

        raise ValueError(
            "Cash flow intelligence contains "
            "duplicate or missing company IDs."
        )

    # --------------------------------------------------------------
    # Save Excel
    # --------------------------------------------------------------

    output.to_excel(
        INTELLIGENCE_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # Distress alerts
    # --------------------------------------------------------------

    distress_rows = result[
        result["distress_flag"]
        == True
    ].copy()

    distress_output = (
        distress_rows[
            [
                "company_id",
                "sector",
                "_latest_cfo",
                "_latest_cff",
                "_latest_net_profit",
            ]
        ]
        .rename(
            columns={
                "_latest_cfo": "cfo",
                "_latest_cff": "cff",
                "_latest_net_profit": (
                    "latest_net_profit"
                ),
            }
        )
        .reset_index(drop=True)
    )

    distress_output.to_csv(
        DISTRESS_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    print("=" * 72)
    print(
        "SPRINT 5 — DAY 31 "
        "CASH FLOW INTELLIGENCE"
    )
    print("=" * 72)

    print(
        f"Official companies : "
        f"{len(companies)}"
    )

    print(
        f"Output rows        : "
        f"{len(output)}"
    )

    print(
        f"Unique companies   : "
        f"{output['company_id'].nunique()}"
    )

    print(
        f"Distress alerts    : "
        f"{len(distress_output)}"
    )

    print(
        f"Deleveraging flags : "
        f"{int(output['deleveraging_flag'].sum())}"
    )

    print(
        f"Excel output       : "
        f"{INTELLIGENCE_FILE}"
    )

    print(
        f"Distress output    : "
        f"{DISTRESS_FILE}"
    )

    print()
    print("Capital allocation distribution:")

    print(
        output[
            "capital_allocation_label"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print()
    print("CFO quality distribution:")

    print(
        output[
            "cfo_quality_label"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print()
    print(
        "Required columns:"
    )

    print(
        ", ".join(
            output.columns
        )
    )

    print("=" * 72)
    print(
        "DAY 31 CASH FLOW INTELLIGENCE "
        "COMPLETED"
    )
    print("=" * 72)

    return output


# ==================================================================
# ENTRY POINT
# ==================================================================

if __name__ == "__main__":

    generate()