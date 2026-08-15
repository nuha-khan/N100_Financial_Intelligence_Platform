"""
Sprint 5 Day 30 - Rule-Based Pros/Cons Generator

Generates company-level Pros and Cons using the 12 Pro rules
and 12 Con rules defined for Sprint 5.

Design principles:
- The `companies` table is the official 92-company universe.
- Sector information comes from the `sectors` table.
- Supporting tables are restricted to those 92 companies.
- No synthetic financial values are generated.
- Only rules actually satisfied by database data produce signals.
- Only signals with confidence_pct > 60 are written.
- Missing Pro/Con coverage is reported honestly in the audit.
"""

from pathlib import Path
import sqlite3
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

DB_PATH = Path("data/nifty100.db")

OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "pros_cons_generated.csv"
COVERAGE_FILE = OUTPUT_DIR / "pros_cons_coverage.csv"

EXPECTED_COMPANIES = 92
MIN_CONFIDENCE = 60.0


# ------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------

def latest_year(df: pd.DataFrame) -> pd.DataFrame:
    """Return the latest available record for each company."""

    if df.empty:
        return df.copy()

    result = df.copy()

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce",
    )

    result = result.dropna(subset=["year"])

    return (
        result
        .sort_values(["company_id", "year"])
        .drop_duplicates(
            "company_id",
            keep="last",
        )
        .reset_index(drop=True)
    )


def clean_numeric(
    df: pd.DataFrame,
    columns: List[str],
) -> pd.DataFrame:
    """Convert selected columns to numeric."""

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
    """Return chronological records for one company."""

    if df.empty:
        return df.copy()

    result = df[
        df["company_id"] == company_id
    ].copy()

    if "year" in result.columns:
        result["year"] = pd.to_numeric(
            result["year"],
            errors="coerce",
        )

        result = result.dropna(
            subset=["year"]
        )

        result = result.sort_values(
            "year"
        )

    return result.reset_index(drop=True)


def consecutive_positive(
    values: pd.Series,
    years: int,
) -> bool:
    """Check whether the latest N valid observations are positive."""

    values = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if len(values) < years:
        return False

    return bool(
        (values.tail(years) > 0).all()
    )


def consecutive_negative(
    values: pd.Series,
    years: int,
) -> bool:
    """Check whether the latest N valid observations are negative."""

    values = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if len(values) < years:
        return False

    return bool(
        (values.tail(years) < 0).all()
    )


def three_year_increase(
    values: pd.Series,
) -> bool:
    """Check for strict increase across the latest three valid observations."""

    values = (
        pd.to_numeric(
            values,
            errors="coerce",
        )
        .dropna()
        .tail(3)
    )

    if len(values) != 3:
        return False

    return bool(
        values.iloc[0]
        < values.iloc[1]
        < values.iloc[2]
    )


def three_year_decline(
    values: pd.Series,
) -> bool:
    """Check for strict decline across the latest three valid observations."""

    values = (
        pd.to_numeric(
            values,
            errors="coerce",
        )
        .dropna()
        .tail(3)
    )

    if len(values) != 3:
        return False

    return bool(
        values.iloc[0]
        > values.iloc[1]
        > values.iloc[2]
    )


# ------------------------------------------------------------------
# Confidence scoring
# ------------------------------------------------------------------

def threshold_confidence(
    value: float,
    threshold: float,
    direction: str,
) -> float:
    """
    Deterministic confidence score for threshold rules.

    A qualifying signal starts at 65 and increases with
    the strength of the observed deviation from the threshold.
    """

    if pd.isna(value):
        return 0.0

    value = float(value)
    threshold = float(threshold)

    if direction == "above":

        if value <= threshold:
            return 0.0

        denominator = max(
            abs(threshold),
            1.0,
        )

        strength = (
            value - threshold
        ) / denominator

    elif direction == "below":

        if value >= threshold:
            return 0.0

        denominator = max(
            abs(threshold),
            1.0,
        )

        strength = (
            threshold - value
        ) / denominator

    else:
        raise ValueError(
            "direction must be 'above' or 'below'"
        )

    confidence = (
        65.0
        + 35.0
        * min(
            max(strength, 0.0),
            1.0,
        )
    )

    return round(
        min(confidence, 100.0),
        2,
    )


def boolean_confidence(
    strength: float = 1.0,
) -> float:
    """Confidence score for a satisfied multi-year rule."""

    strength = min(
        max(float(strength), 0.0),
        1.0,
    )

    return round(
        65.0 + 35.0 * strength,
        2,
    )


# ------------------------------------------------------------------
# Database loading
# ------------------------------------------------------------------

def load_data() -> Tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Load all tables required by the Day 30 rules.

    The companies table defines the official universe.
    The sectors table supplies broad-sector classification.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)

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
                sub_sector,
                index_weight_pct,
                market_cap_category
            FROM sectors
            """,
            connection,
        )

        ratios = pd.read_sql_query(
            "SELECT * FROM financial_ratios",
            connection,
        )

        pnl = pd.read_sql_query(
            "SELECT * FROM profitandloss",
            connection,
        )

        balancesheet = pd.read_sql_query(
            "SELECT * FROM balancesheet",
            connection,
        )

        cashflow = pd.read_sql_query(
            "SELECT * FROM cashflow",
            connection,
        )

        market_cap = pd.read_sql_query(
            "SELECT * FROM market_cap",
            connection,
        )

    finally:
        connection.close()

    # --------------------------------------------------------------
    # Validate official company universe
    # --------------------------------------------------------------

    unique_companies = (
        companies["company_id"]
        .nunique()
    )

    if (
        len(companies) != EXPECTED_COMPANIES
        or unique_companies != EXPECTED_COMPANIES
    ):
        raise ValueError(
            "Official companies table must contain exactly "
            f"{EXPECTED_COMPANIES} unique companies. "
            f"Found {len(companies)} rows and "
            f"{unique_companies} unique IDs."
        )

    official_ids = set(
        companies["company_id"]
    )

    # --------------------------------------------------------------
    # Validate sector mapping
    # --------------------------------------------------------------

    sectors = sectors[
        sectors["company_id"].isin(
            official_ids
        )
    ].copy()

    sector_duplicates = (
        sectors["company_id"]
        .duplicated()
        .any()
    )

    if sector_duplicates:
        raise ValueError(
            "The sectors table contains multiple "
            "sector records for at least one company. "
            "A single company-level sector mapping is required."
        )

    # --------------------------------------------------------------
    # Restrict analytical tables to official universe
    # --------------------------------------------------------------

    ratios = ratios[
        ratios["company_id"].isin(
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

    cashflow = cashflow[
        cashflow["company_id"].isin(
            official_ids
        )
    ].copy()

    market_cap = market_cap[
        market_cap["company_id"].isin(
            official_ids
        )
    ].copy()

    # --------------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------------

    ratios = clean_numeric(
        ratios,
        [
            "year",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "debt_to_equity",
            "interest_coverage",
            "net_debt_cr",
            "operating_profit_margin_pct",
            "free_cash_flow_cr",
            "revenue_cagr_5y",
            "pat_cagr_5y",
            "eps_cagr_5y",
            "dividend_payout_ratio_pct",
        ],
    )

    pnl = clean_numeric(
        pnl,
        [
            "year",
            "sales",
            "operating_profit",
            "net_profit",
            "eps",
            "dividend_payout",
        ],
    )

    balancesheet = clean_numeric(
        balancesheet,
        [
            "year",
            "borrowings",
            "total_assets",
        ],
    )

    cashflow = clean_numeric(
        cashflow,
        [
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
        ],
    )

    market_cap = clean_numeric(
        market_cap,
        [
            "year",
            "dividend_yield_pct",
        ],
    )

    return (
        companies,
        sectors,
        ratios,
        pnl,
        balancesheet,
        cashflow,
        market_cap,
    )


# ------------------------------------------------------------------
# Company rule evaluation
# ------------------------------------------------------------------

def evaluate_company(
    company_id: str,
    latest_ratio: pd.Series,
    broad_sector: str,
    ratio_history: pd.DataFrame,
    pnl_history: pd.DataFrame,
    balance_history: pd.DataFrame,
    cashflow_history: pd.DataFrame,
    market_history: pd.DataFrame,
) -> List[Dict]:
    """Evaluate all 12 Pro and 12 Con rules."""

    signals: List[Dict] = []

    def add_signal(
        rule_id: str,
        signal_type: str,
        text: str,
        confidence: float,
    ) -> None:

        if confidence > MIN_CONFIDENCE:
            signals.append(
                {
                    "company_id": company_id,
                    "type": signal_type,
                    "rule_id": rule_id,
                    "text": text,
                    "confidence_pct": round(
                        float(confidence),
                        2,
                    ),
                }
            )

    # --------------------------------------------------------------
    # Latest ratio metrics
    # --------------------------------------------------------------

    roe = latest_ratio.get(
        "return_on_equity_pct",
        np.nan,
    )

    roce = latest_ratio.get(
        "return_on_capital_employed_pct",
        np.nan,
    )

    debt_to_equity = latest_ratio.get(
        "debt_to_equity",
        np.nan,
    )

    interest_coverage = latest_ratio.get(
        "interest_coverage",
        np.nan,
    )

    opm = latest_ratio.get(
        "operating_profit_margin_pct",
        np.nan,
    )

    net_debt = latest_ratio.get(
        "net_debt_cr",
        np.nan,
    )

    revenue_cagr = latest_ratio.get(
        "revenue_cagr_5y",
        np.nan,
    )

    pat_cagr = latest_ratio.get(
        "pat_cagr_5y",
        np.nan,
    )

    eps_cagr = latest_ratio.get(
        "eps_cagr_5y",
        np.nan,
    )

    payout_ratio = latest_ratio.get(
        "dividend_payout_ratio_pct",
        np.nan,
    )

    # --------------------------------------------------------------
    # Latest P&L
    # --------------------------------------------------------------

    if pnl_history.empty:

        latest_pat = np.nan
        latest_operating_profit = np.nan

    else:

        latest_pnl = (
            pnl_history
            .sort_values("year")
            .iloc[-1]
        )

        latest_pat = latest_pnl.get(
            "net_profit",
            np.nan,
        )

        latest_operating_profit = (
            latest_pnl.get(
                "operating_profit",
                np.nan,
            )
        )

    # --------------------------------------------------------------
    # FCF history
    #
    # Use the financial_ratios FCF metric when available.
    # Otherwise derive FCF from cash flow as:
    #
    # Operating Activity + Investing Activity
    #
    # This is consistent with the project cash-flow convention.
    # --------------------------------------------------------------

    if (
        not ratio_history.empty
        and "free_cash_flow_cr" in ratio_history.columns
    ):

        ratio_fcf = ratio_history[
            [
                "year",
                "free_cash_flow_cr",
            ]
        ].copy()

        ratio_fcf = ratio_fcf.dropna(
            subset=["free_cash_flow_cr"]
        )

    else:

        ratio_fcf = pd.DataFrame()

    if not cashflow_history.empty:

        cf = cashflow_history[
            [
                "year",
                "operating_activity",
                "investing_activity",
            ]
        ].copy()

        cf["derived_fcf"] = (
            cf["operating_activity"]
            + cf["investing_activity"]
        )

    else:

        cf = pd.DataFrame()

    # Prefer the project's calculated FCF metric.
    if not ratio_fcf.empty:

        fcf_history = (
            ratio_fcf
            .sort_values("year")
            .drop_duplicates(
                "year",
                keep="last",
            )
            ["free_cash_flow_cr"]
        )

        latest_fcf = float(
            fcf_history.iloc[-1]
        )

    elif not cf.empty:

        fcf_history = (
            cf.sort_values("year")
            ["derived_fcf"]
            .dropna()
        )

        latest_fcf = float(
            fcf_history.iloc[-1]
        )

    else:

        fcf_history = pd.Series(
            dtype=float
        )

        latest_fcf = np.nan

    # --------------------------------------------------------------
    # Dividend yield
    # --------------------------------------------------------------

    if not market_history.empty:

        latest_market = (
            market_history
            .sort_values("year")
            .iloc[-1]
        )

        dividend_yield = latest_market.get(
            "dividend_yield_pct",
            np.nan,
        )

    else:

        dividend_yield = np.nan

    # ==============================================================
    # PROS
    # ==============================================================

    # --------------------------------------------------------------
    # P1 — ROE > 20% sustained for 3+ years
    # --------------------------------------------------------------

    roe_history = ratio_history[
        "return_on_equity_pct"
    ].dropna()

    if consecutive_positive(
        roe_history - 20,
        3,
    ):

        excess = (
            float(
                roe_history.tail(3).mean()
            )
            - 20
        )

        add_signal(
            "P1",
            "pro",
            "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
            boolean_confidence(
                min(
                    excess / 20,
                    1,
                )
            ),
        )

    # --------------------------------------------------------------
    # P2 — FCF positive for 5+ consecutive years
    # --------------------------------------------------------------

    if consecutive_positive(
        fcf_history,
        5,
    ):

        add_signal(
            "P2",
            "pro",
            "Strong free cash flow generation over 5 years signals healthy business fundamentals",
            boolean_confidence(),
        )

    # --------------------------------------------------------------
    # P3 — D/E = 0
    # --------------------------------------------------------------

    if (
        pd.notna(debt_to_equity)
        and abs(
            float(debt_to_equity)
        ) <= 1e-9
    ):

        add_signal(
            "P3",
            "pro",
            "Debt-free balance sheet provides financial flexibility and eliminates conventional debt burden",
            100.0,
        )

    # --------------------------------------------------------------
    # P4 — Revenue CAGR > 15%
    # --------------------------------------------------------------

    if (
        pd.notna(revenue_cagr)
        and float(revenue_cagr) > 15
    ):

        add_signal(
            "P4",
            "pro",
            "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
            threshold_confidence(
                float(revenue_cagr),
                15,
                "above",
            ),
        )

    # --------------------------------------------------------------
    # P5 — OPM > 25%
    # --------------------------------------------------------------

    if (
        pd.notna(opm)
        and float(opm) > 25
    ):

        add_signal(
            "P5",
            "pro",
            "Operating profit margin above 25% indicates strong pricing power and cost discipline",
            threshold_confidence(
                float(opm),
                25,
                "above",
            ),
        )

    # --------------------------------------------------------------
    # P6 — PAT CAGR > 20%
    # --------------------------------------------------------------

    if (
        pd.notna(pat_cagr)
        and float(pat_cagr) > 20
    ):

        add_signal(
            "P6",
            "pro",
            "Net profit compounding at above 20% over 5 years creates significant shareholder value",
            threshold_confidence(
                float(pat_cagr),
                20,
                "above",
            ),
        )

    # --------------------------------------------------------------
    # P7 — ICR > 10
    #
    # Debt-free companies are already captured by P3.
    # We do NOT describe a debt-free company as having
    # "very high interest coverage" when ICR is unavailable.
    # --------------------------------------------------------------

    if (
        pd.notna(interest_coverage)
        and float(interest_coverage) > 10
    ):

        add_signal(
            "P7",
            "pro",
            "Interest coverage above 10x indicates strong capacity to service debt obligations",
            threshold_confidence(
                float(interest_coverage),
                10,
                "above",
            ),
        )

    # --------------------------------------------------------------
    # P8 — Dividend yield > 2% AND positive FCF
    # --------------------------------------------------------------

    if (
        pd.notna(dividend_yield)
        and float(dividend_yield) > 2
        and pd.notna(latest_fcf)
        and float(latest_fcf) > 0
    ):

        add_signal(
            "P8",
            "pro",
            "Dividend yield above 2% is supported by positive free cash flow",
            threshold_confidence(
                float(dividend_yield),
                2,
                "above",
            ),
        )

    # --------------------------------------------------------------
    # P9 — EPS CAGR > 15%
    # --------------------------------------------------------------

    if (
        pd.notna(eps_cagr)
        and float(eps_cagr) > 15
    ):

        add_signal(
            "P9",
            "pro",
            "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
            threshold_confidence(
                float(eps_cagr),
                15,
                "above",
            ),
        )

    # --------------------------------------------------------------
    # P10 — ROE improving for 3 consecutive years
    # --------------------------------------------------------------

    if three_year_increase(
        roe_history
    ):

        add_signal(
            "P10",
            "pro",
            "Return on equity improving for 3 consecutive years shows strengthening business quality",
            boolean_confidence(),
        )

    # --------------------------------------------------------------
    # P11 — PAT CAGR > Revenue CAGR
    # --------------------------------------------------------------

    if (
        pd.notna(revenue_cagr)
        and pd.notna(pat_cagr)
        and float(pat_cagr)
        > float(revenue_cagr)
    ):

        spread = (
            float(pat_cagr)
            - float(revenue_cagr)
        )

        add_signal(
            "P11",
            "pro",
            "Revenue growing slower than profits shows improving operating leverage and scale benefits",
            boolean_confidence(
                min(
                    spread / 15,
                    1,
                )
            ),
        )

    # --------------------------------------------------------------
    # P12 — Assets growing AND borrowings declining
    # --------------------------------------------------------------

    if len(balance_history) >= 2:

        previous = (
            balance_history.iloc[-2]
        )

        current = (
            balance_history.iloc[-1]
        )

        if (
            pd.notna(
                previous.get(
                    "total_assets",
                    np.nan,
                )
            )
            and pd.notna(
                current.get(
                    "total_assets",
                    np.nan,
                )
            )
            and pd.notna(
                previous.get(
                    "borrowings",
                    np.nan,
                )
            )
            and pd.notna(
                current.get(
                    "borrowings",
                    np.nan,
                )
            )
            and current["total_assets"]
            > previous["total_assets"]
            and current["borrowings"]
            < previous["borrowings"]
        ):

            add_signal(
                "P12",
                "pro",
                "Growing asset base alongside declining borrowings indicates improving balance-sheet strength",
                boolean_confidence(),
            )

    # ==============================================================
    # CONS
    # ==============================================================

    # --------------------------------------------------------------
    # C1 — D/E > 2 for non-financial companies
    # --------------------------------------------------------------

    financial_sectors = {
        "Financials",
        "Financial Services",
        "Banks",
        "Insurance",
    }

    if (
        broad_sector not in financial_sectors
        and pd.notna(debt_to_equity)
        and float(debt_to_equity) > 2
    ):

        add_signal(
            "C1",
            "con",
            f"Debt-to-equity ratio of {float(debt_to_equity):.2f} is elevated for a non-financial company and warrants monitoring",
            threshold_confidence(
                float(debt_to_equity),
                2,
                "above",
            ),
        )

    # --------------------------------------------------------------
    # C2 — FCF negative for 3 consecutive years
    # --------------------------------------------------------------

    if consecutive_negative(
        fcf_history,
        3,
    ):

        add_signal(
            "C2",
            "con",
            "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
            boolean_confidence(),
        )

    # --------------------------------------------------------------
    # C3 — OPM declining for 3 consecutive years
    # --------------------------------------------------------------

    opm_history = ratio_history[
        "operating_profit_margin_pct"
    ].dropna()

    if three_year_decline(
        opm_history
    ):

        add_signal(
            "C3",
            "con",
            "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
            boolean_confidence(),
        )

    # --------------------------------------------------------------
    # C4 — Latest net profit negative
    # --------------------------------------------------------------

    if (
        pd.notna(latest_pat)
        and float(latest_pat) < 0
    ):

        add_signal(
            "C4",
            "con",
            "Company reported a net loss in the most recent financial year",
            100.0,
        )

    # --------------------------------------------------------------
    # C5 — Revenue declining for 2 consecutive years
    # --------------------------------------------------------------

    sales_history = (
        pnl_history[
            "sales"
        ]
        .dropna()
    )

    if len(sales_history) >= 3:

        latest_three = (
            sales_history.tail(3)
        )

        if (
            latest_three.iloc[0]
            > latest_three.iloc[1]
            > latest_three.iloc[2]
        ):

            add_signal(
                "C5",
                "con",
                "Revenue contraction over 2 consecutive years indicates demand weakness or market share pressure",
                boolean_confidence(),
            )

    # --------------------------------------------------------------
    # C6 — ICR < 1.5
    # --------------------------------------------------------------

    if (
        pd.notna(interest_coverage)
        and float(interest_coverage) < 1.5
    ):

        add_signal(
            "C6",
            "con",
            "Interest coverage ratio below 1.5x indicates elevated debt-servicing risk",
            threshold_confidence(
                float(interest_coverage),
                1.5,
                "below",
            ),
        )

    # --------------------------------------------------------------
    # C7 — Dividend payout > 100%
    # --------------------------------------------------------------

    if (
        pd.notna(payout_ratio)
        and float(payout_ratio) > 100
    ):

        add_signal(
            "C7",
            "con",
            "Dividend payout ratio above 100% indicates dividends exceed reported earnings and may be difficult to sustain",
            threshold_confidence(
                float(payout_ratio),
                100,
                "above",
            ),
        )

    # --------------------------------------------------------------
    # C8 — D/E rising for 3 consecutive years
    # --------------------------------------------------------------

    debt_history = ratio_history[
        "debt_to_equity"
    ].dropna()

    if three_year_increase(
        debt_history
    ):

        add_signal(
            "C8",
            "con",
            "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
            boolean_confidence(),
        )

    # --------------------------------------------------------------
    # C9 — EPS declining for 3 consecutive years
    # --------------------------------------------------------------

    eps_history = (
        pnl_history[
            "eps"
        ]
        .dropna()
    )

    if three_year_decline(
        eps_history
    ):

        add_signal(
            "C9",
            "con",
            "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
            boolean_confidence(),
        )

    # --------------------------------------------------------------
    # C10 — ROCE < 10%
    # --------------------------------------------------------------

    if (
        pd.notna(roce)
        and float(roce) < 10
    ):

        add_signal(
            "C10",
            "con",
            "Return on capital employed below 10% suggests weak returns on deployed capital",
            threshold_confidence(
                float(roce),
                10,
                "below",
            ),
        )

    # --------------------------------------------------------------
    # C11 — Net debt > 3x EBITDA proxy
    #
    # The project's available P&L schema contains operating_profit,
    # not a separate EBITDA column.
    #
    # Therefore operating profit is used as the project's existing
    # EBITDA proxy. This is explicitly documented rather than hidden.
    # --------------------------------------------------------------

    if (
        pd.notna(net_debt)
        and pd.notna(latest_operating_profit)
        and float(latest_operating_profit) > 0
    ):

        net_debt_to_ebitda_proxy = (
            float(net_debt)
            / float(latest_operating_profit)
        )

        if net_debt_to_ebitda_proxy > 3:

            add_signal(
                "C11",
                "con",
                "Net debt exceeds 3 times the project's operating-profit EBITDA proxy, indicating elevated leverage",
                threshold_confidence(
                    net_debt_to_ebitda_proxy,
                    3,
                    "above",
                ),
            )

    # --------------------------------------------------------------
    # C12 — Revenue CAGR < 5%
    # --------------------------------------------------------------

    if (
        pd.notna(revenue_cagr)
        and float(revenue_cagr) < 5
    ):

        add_signal(
            "C12",
            "con",
            "Revenue growing below 5% CAGR over 5 years indicates limited business momentum",
            threshold_confidence(
                float(revenue_cagr),
                5,
                "below",
            ),
        )

    return signals


# ------------------------------------------------------------------
# Main generation
# ------------------------------------------------------------------

def generate() -> pd.DataFrame:
    """Generate Pros/Cons output and coverage audit."""

    (
        companies,
        sectors,
        ratios,
        pnl,
        balancesheet,
        cashflow,
        market_cap,
    ) = load_data()

    latest_ratios = latest_year(
        ratios
    )

    latest_ratio_map = (
        latest_ratios
        .set_index("company_id")
    )

    sector_map = (
        sectors
        .set_index("company_id")
    )

    all_signals: List[Dict] = []

    for company_id in companies[
        "company_id"
    ]:

        ratio_history = company_history(
            ratios,
            company_id,
        )

        pnl_history = company_history(
            pnl,
            company_id,
        )

        balance_history = company_history(
            balancesheet,
            company_id,
        )

        cashflow_history = company_history(
            cashflow,
            company_id,
        )

        market_history = company_history(
            market_cap,
            company_id,
        )

        if company_id in latest_ratio_map.index:

            latest_ratio = (
                latest_ratio_map.loc[
                    company_id
                ]
            )

        else:

            latest_ratio = pd.Series(
                dtype=float
            )

        if company_id in sector_map.index:

            broad_sector = str(
                sector_map.loc[
                    company_id,
                    "broad_sector",
                ]
            )

        else:

            broad_sector = ""

        company_signals = evaluate_company(
            company_id=company_id,
            latest_ratio=latest_ratio,
            broad_sector=broad_sector,
            ratio_history=ratio_history,
            pnl_history=pnl_history,
            balance_history=balance_history,
            cashflow_history=cashflow_history,
            market_history=market_history,
        )

        all_signals.extend(
            company_signals
        )

    result = pd.DataFrame(
        all_signals,
        columns=[
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct",
        ],
    )

    if result.empty:
        result = pd.DataFrame(
            columns=[
                "company_id",
                "type",
                "rule_id",
                "text",
                "confidence_pct",
            ]
        )
    else:
        result = (
            result
            .drop_duplicates(
                subset=[
                    "company_id",
                    "type",
                    "rule_id",
                ]
            )
            .sort_values(
                [
                    "company_id",
                    "type",
                    "rule_id",
                ]
            )
            .reset_index(drop=True)
        )

    # --------------------------------------------------------------
    # Output directory
    # --------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # Coverage audit
    # --------------------------------------------------------------

    pro_counts = (
        result[
            result["type"] == "pro"
        ]
        .groupby("company_id")
        .size()
    )

    con_counts = (
        result[
            result["type"] == "con"
        ]
        .groupby("company_id")
        .size()
    )

    coverage = companies.copy()

    coverage = coverage.merge(
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

    coverage["pro_count"] = (
        coverage["company_id"]
        .map(pro_counts)
        .fillna(0)
        .astype(int)
    )

    coverage["con_count"] = (
        coverage["company_id"]
        .map(con_counts)
        .fillna(0)
        .astype(int)
    )

    coverage["has_pro"] = (
        coverage["pro_count"] > 0
    )

    coverage["has_con"] = (
        coverage["con_count"] > 0
    )

    coverage["coverage_status"] = np.where(
        coverage["has_pro"]
        & coverage["has_con"],
        "PASS",
        "REVIEW",
    )

    coverage.to_csv(
        COVERAGE_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # Validation summary
    # --------------------------------------------------------------

    companies_with_pro = int(
        coverage["has_pro"].sum()
    )

    companies_with_con = int(
        coverage["has_con"].sum()
    )

    missing_pro = coverage.loc[
        ~coverage["has_pro"],
        "company_id",
    ].tolist()

    missing_con = coverage.loc[
        ~coverage["has_con"],
        "company_id",
    ].tolist()

    print("=" * 72)
    print(
        "SPRINT 5 — DAY 30 "
        "PROS/CONS GENERATOR"
    )
    print("=" * 72)

    print(
        f"Official companies : "
        f"{len(companies)}"
    )

    print(
        f"Generated signals  : "
        f"{len(result)}"
    )

    print(
        f"Pros               : "
        f"{(result['type'] == 'pro').sum()}"
    )

    print(
        f"Cons               : "
        f"{(result['type'] == 'con').sum()}"
    )

    print(
        f"Companies with Pro : "
        f"{companies_with_pro}/"
        f"{EXPECTED_COMPANIES}"
    )

    print(
        f"Companies with Con : "
        f"{companies_with_con}/"
        f"{EXPECTED_COMPANIES}"
    )

    print(
        f"Output             : "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Coverage audit     : "
        f"{COVERAGE_FILE}"
    )

    if missing_pro:

        print(
            "\nCompanies without "
            "a qualifying Pro rule:"
        )

        print(
            ", ".join(
                missing_pro
            )
        )

    if missing_con:

        print(
            "\nCompanies without "
            "a qualifying Con rule:"
        )

        print(
            ", ".join(
                missing_con
            )
        )

    print("=" * 72)

    return result


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    generate()