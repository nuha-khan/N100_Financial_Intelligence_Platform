"""
Portfolio API routes.

Provides portfolio-oriented market and financial metrics
for N100 companies.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.database import DB_PATH


# ---------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/portfolio",
    tags=["Portfolio"],
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
# PORTFOLIO STATISTICS
# ---------------------------------------------------------------------

@router.get("/stats")
def get_portfolio_stats():
    """Return aggregate portfolio statistics across N100 companies."""

    connection = get_db_connection()

    try:
        total_companies = connection.execute(
            """
            SELECT COUNT(DISTINCT company_id)
            FROM financial_ratios
            """
        ).fetchone()[0]

        latest_year = connection.execute(
            """
            SELECT MAX(year)
            FROM financial_ratios
            """
        ).fetchone()[0]

        stats = connection.execute(
            """
            SELECT
                ROUND(AVG(return_on_equity_pct), 2) AS average_roe_pct,
                ROUND(AVG(net_profit_margin_pct), 2) AS average_npm_pct,
                ROUND(AVG(debt_to_equity), 2) AS average_debt_to_equity,
                ROUND(AVG(interest_coverage), 2) AS average_interest_coverage,
                ROUND(SUM(free_cash_flow_cr), 2) AS total_free_cash_flow_cr
            FROM financial_ratios
            WHERE year = ?
            """,
            (latest_year,),
        ).fetchone()

    finally:
        connection.close()

    return {
        "total_companies": total_companies,
        "latest_year": latest_year,
        "statistics": dict(stats) if stats else {},
    }

# ---------------------------------------------------------------------
# COMPANY PORTFOLIO SNAPSHOT
# ---------------------------------------------------------------------

@router.get("/{company_id}")
def get_portfolio_snapshot(company_id: str):
    """
    Return the latest market price and latest financial metrics
    for a company.
    """

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

        market = connection.execute(
            """
            SELECT
                date,
                close_price,
                adjusted_close,
                volume
            FROM stock_prices
            WHERE company_id = ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

        financials = connection.execute(
            """
            SELECT
                year,
                net_profit_margin_pct,
                operating_profit_margin_pct,
                return_on_equity_pct,
                debt_to_equity,
                interest_coverage,
                free_cash_flow_cr,
                earnings_per_share,
                dividend_payout_ratio_pct
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

    finally:
        connection.close()

    if market is None and financials is None:
        raise HTTPException(
            status_code=404,
            detail=f"No portfolio data found for '{company_id}'.",
        )

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "latest_market_data": dict(market) if market else None,
        "latest_financials": dict(financials) if financials else None,
    }


# ---------------------------------------------------------------------
# PRICE HISTORY
# ---------------------------------------------------------------------

@router.get("/{company_id}/prices")
def get_price_history(company_id: str):
    """Return historical stock prices for a company."""

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
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                adjusted_close
            FROM stock_prices
            WHERE company_id = ?
            ORDER BY date
            """,
            (company_id,),
        ).fetchall()

        prices = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "count": len(prices),
        "prices": prices,
    }


# ---------------------------------------------------------------------
# FINANCIAL HISTORY
# ---------------------------------------------------------------------

@router.get("/{company_id}/financials")
def get_financial_history(company_id: str):
    """Return historical financial metrics for a company."""

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
                net_profit_margin_pct,
                operating_profit_margin_pct,
                return_on_equity_pct,
                debt_to_equity,
                interest_coverage,
                free_cash_flow_cr,
                capex_cr,
                earnings_per_share,
                book_value_per_share,
                dividend_payout_ratio_pct,
                total_debt_cr,
                cash_from_operations_cr
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year
            """,
            (company_id,),
        ).fetchall()

        financials = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "count": len(financials),
        "financials": financials,
    }