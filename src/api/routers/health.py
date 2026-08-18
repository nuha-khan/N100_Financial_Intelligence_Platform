"""
Health API routes.

Provides:
1. API/database health check
2. Company financial health score
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.database import DB_PATH
from src.analytics.ratios import composite_quality_score


router = APIRouter(
    prefix="/api/v1",
    tags=["Health"],
)


# ---------------------------------------------------------------------
# SYSTEM HEALTH
# ---------------------------------------------------------------------

@router.get("/health")
def health_check():
    """Check API and database health."""

    connection = sqlite3.connect(DB_PATH)

    try:
        tables = [
            "companies",
            "financial_ratios",
            "company_growth_metrics",
            "sectors",
        ]

        counts = {}

        for table in tables:
            row = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()

            counts[table] = row[0]

    finally:
        connection.close()

    return {
        "status": "ok",
        "database": "connected",
        "tables": counts,
    }


# ---------------------------------------------------------------------
# COMPANY FINANCIAL HEALTH
# ---------------------------------------------------------------------

@router.get("/health/{company_id}")
def get_company_health(company_id: str):
    """
    Return the financial health score for a company.

    The score uses the existing Composite Quality Score logic:
    - ROE: 30 points
    - ROCE: 30 points
    - Revenue CAGR (5Y): 20 points
    - Debt-to-Equity: 20 points
    """

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        query = """
            SELECT
                fr.company_id,
                fr.year,
                fr.return_on_equity_pct,
                c.roce_percentage,
                gm.revenue_cagr_5y,
                fr.debt_to_equity
            FROM financial_ratios fr
            JOIN companies c
                ON fr.company_id = c.id
            JOIN company_growth_metrics gm
                ON fr.company_id = gm.company_id
            WHERE fr.company_id = ?
            ORDER BY fr.year DESC
            LIMIT 1
        """

        row = connection.execute(
            query,
            (company_id.upper(),),
        ).fetchone()

    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{company_id.upper()}' not found",
        )

    score = composite_quality_score(
        row["return_on_equity_pct"],
        row["roce_percentage"],
        row["revenue_cagr_5y"],
        row["debt_to_equity"],
    )

    # Health band classification
    if score >= 80:
        health_band = "Excellent"
    elif score >= 60:
        health_band = "Good"
    elif score >= 40:
        health_band = "Average"
    elif score >= 20:
        health_band = "Weak"
    else:
        health_band = "Poor"

    return {
        "company_id": row["company_id"],
        "year": row["year"],
        "roe": row["return_on_equity_pct"],
        "roce": row["roce_percentage"],
        "revenue_cagr_5y": row["revenue_cagr_5y"],
        "debt_to_equity": row["debt_to_equity"],
        "health_score": score,
        "health_band": health_band,
    }