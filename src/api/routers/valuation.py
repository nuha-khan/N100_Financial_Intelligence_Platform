"""
Valuation API routes.

Provides valuation and market-cap information for N100 companies.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.database import DB_PATH


# ---------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/valuation",
    tags=["Valuation"],
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
# LATEST VALUATION
# ---------------------------------------------------------------------

@router.get("/{company_id}")
def get_company_valuation(company_id: str):
    """Return the latest available valuation metrics for a company."""

    connection = get_db_connection()

    try:
        company = connection.execute(
            """
            SELECT
                id AS company_id,
                company_name
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found.",
            )

        valuation = connection.execute(
            """
            SELECT
                company_id,
                year,
                market_cap_crore,
                enterprise_value_crore,
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield_pct
            FROM market_cap
            WHERE company_id = ?
            ORDER BY year DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

    finally:
        connection.close()

    if valuation is None:
        raise HTTPException(
            status_code=404,
            detail=f"No valuation data found for '{company_id}'.",
        )

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "valuation": dict(valuation),
    }


# ---------------------------------------------------------------------
# VALUATION HISTORY
# ---------------------------------------------------------------------

@router.get("/{company_id}/history")
def get_valuation_history(company_id: str):
    """Return historical valuation metrics for a company."""

    connection = get_db_connection()

    try:
        company = connection.execute(
            """
            SELECT
                id AS company_id,
                company_name
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found.",
            )

        rows = connection.execute(
            """
            SELECT
                year,
                market_cap_crore,
                enterprise_value_crore,
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield_pct
            FROM market_cap
            WHERE company_id = ?
            ORDER BY year
            """,
            (company_id,),
        ).fetchall()

        history = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "count": len(history),
        "history": history,
    }


# ---------------------------------------------------------------------
# GROWTH & VALUATION SUMMARY
# ---------------------------------------------------------------------

@router.get("/{company_id}/summary")
def get_valuation_summary(company_id: str):
    """Return valuation metrics together with available growth metrics."""

    connection = get_db_connection()

    try:
        company = connection.execute(
            """
            SELECT
                id AS company_id,
                company_name
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found.",
            )

        valuation = connection.execute(
            """
            SELECT
                year,
                market_cap_crore,
                enterprise_value_crore,
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield_pct
            FROM market_cap
            WHERE company_id = ?
            ORDER BY year DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

        growth = connection.execute(
            """
            SELECT
                compounded_sales_growth,
                compounded_profit_growth,
                stock_price_cagr,
                roe
            FROM analysis
            WHERE company_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

    finally:
        connection.close()

    if valuation is None and growth is None:
        raise HTTPException(
            status_code=404,
            detail=f"No valuation or analysis data found for '{company_id}'.",
        )

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "valuation": dict(valuation) if valuation else None,
        "growth": dict(growth) if growth else None,
    }