"""
Market Capitalization API routes.

Provides market-cap and valuation information for N100 companies.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.database import DB_PATH


router = APIRouter(
    prefix="/api/v1/market-cap",
    tags=["Market Cap"],
)


def get_db_connection():
    """Create a SQLite database connection."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# ---------------------------------------------------------------------
# GET MARKET CAP BY TICKER
# ---------------------------------------------------------------------

@router.get("/{ticker}")
def get_market_cap(ticker: str):
    """Return latest market-cap information for a company."""

    ticker = ticker.upper()

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
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found.",
            )

        row = connection.execute(
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
            (ticker,),
        ).fetchone()

    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No market-cap data found for '{ticker}'.",
        )

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "market_cap": dict(row),
    }