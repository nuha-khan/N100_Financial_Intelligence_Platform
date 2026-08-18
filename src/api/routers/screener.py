"""
Screener API routes.

Provides endpoints for filtering N100 companies
using financial and growth metrics.
"""

import sqlite3

from fastapi import APIRouter, Query

from src.api.database import DB_PATH


# ---------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/screener",
    tags=["Screener"],
)


# ---------------------------------------------------------------------
# DATABASE HELPER
# ---------------------------------------------------------------------

def get_db_connection():
    """Create a SQLite database connection."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# ---------------------------------------------------------------------
# SCREEN COMPANIES
# ---------------------------------------------------------------------

@router.get("/")
def screen_companies(
    min_roe: float | None = Query(
        default=None,
        description="Minimum Return on Equity (%)",
    ),
    max_debt_to_equity: float | None = Query(
        default=None,
        description="Maximum Debt-to-Equity ratio",
    ),
    min_revenue_cagr: float | None = Query(
        default=None,
        description="Minimum 5-year Revenue CAGR (%)",
    ),
    min_opm: float | None = Query(
        default=None,
        description="Minimum Operating Profit Margin (%)",
    ),
    min_npm: float | None = Query(
        default=None,
        description="Minimum Net Profit Margin (%)",
    ),
    min_interest_coverage: float | None = Query(
        default=None,
        description="Minimum Interest Coverage ratio",
    ),
    min_asset_turnover: float | None = Query(
        default=None,
        description="Minimum Asset Turnover",
    ),
):
    """
    Screen N100 companies using financial filters.

    Only the filters supplied by the user are applied.
    """

    connection = get_db_connection()

    try:
        query = """
            SELECT
                c.id AS company_id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,

                fr.year,

                fr.return_on_equity_pct,
                fr.debt_to_equity,
                fr.operating_profit_margin_pct,
                fr.net_profit_margin_pct,
                fr.interest_coverage,
                fr.asset_turnover,

                gm.revenue_cagr_5y

            FROM companies c

            LEFT JOIN sectors s
                ON c.id = s.company_id

            LEFT JOIN financial_ratios fr
                ON c.id = fr.company_id

            LEFT JOIN company_growth_metrics gm
                ON c.id = gm.company_id

            WHERE fr.year = (
                SELECT MAX(fr2.year)
                FROM financial_ratios fr2
                WHERE fr2.company_id = c.id
            )
        """

        conditions = []
        parameters = []

        # -------------------------------------------------------------
        # FILTERS
        # -------------------------------------------------------------

        if min_roe is not None:
            conditions.append(
                "fr.return_on_equity_pct >= ?"
            )
            parameters.append(min_roe)

        if max_debt_to_equity is not None:
            conditions.append(
                "fr.debt_to_equity <= ?"
            )
            parameters.append(max_debt_to_equity)

        if min_revenue_cagr is not None:
            conditions.append(
                "gm.revenue_cagr_5y >= ?"
            )
            parameters.append(min_revenue_cagr)

        if min_opm is not None:
            conditions.append(
                "fr.operating_profit_margin_pct >= ?"
            )
            parameters.append(min_opm)

        if min_npm is not None:
            conditions.append(
                "fr.net_profit_margin_pct >= ?"
            )
            parameters.append(min_npm)

        if min_interest_coverage is not None:
            conditions.append(
                "fr.interest_coverage >= ?"
            )
            parameters.append(min_interest_coverage)

        if min_asset_turnover is not None:
            conditions.append(
                "fr.asset_turnover >= ?"
            )
            parameters.append(min_asset_turnover)

        # -------------------------------------------------------------
        # BUILD WHERE CLAUSE
        # -------------------------------------------------------------

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += """
            ORDER BY c.company_name
        """

        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

        companies = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "count": len(companies),
        "filters": {
            "min_roe": min_roe,
            "max_debt_to_equity": max_debt_to_equity,
            "min_revenue_cagr": min_revenue_cagr,
            "min_opm": min_opm,
            "min_npm": min_npm,
            "min_interest_coverage": min_interest_coverage,
            "min_asset_turnover": min_asset_turnover,
        },
        "companies": companies,
    }


# ---------------------------------------------------------------------
# SCREENING TEMPLATES
# ---------------------------------------------------------------------

@router.get("/templates")
def get_screener_templates():
    """Return predefined screening templates."""

    templates = [
        {
            "name": "Quality Companies",
            "description": "Companies with strong profitability and low leverage.",
            "filters": {
                "min_roe": 15,
                "max_debt_to_equity": 1,
            },
        },
        {
            "name": "Growth Companies",
            "description": "Companies with strong historical revenue growth.",
            "filters": {
                "min_revenue_cagr": 15,
                "min_roe": 10,
            },
        },
        {
            "name": "High Profitability",
            "description": "Companies with strong operating and net margins.",
            "filters": {
                "min_opm": 20,
                "min_npm": 10,
            },
        },
        {
            "name": "Low Debt",
            "description": "Companies with relatively low financial leverage.",
            "filters": {
                "max_debt_to_equity": 0.5,
                "min_roe": 10,
            },
        },
        {
            "name": "Balanced",
            "description": "Companies combining profitability, growth and manageable debt.",
            "filters": {
                "min_roe": 12,
                "max_debt_to_equity": 1.5,
                "min_revenue_cagr": 10,
            },
        },
    ]

    return {
        "count": len(templates),
        "templates": templates,
    }