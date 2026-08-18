"""
Sectors API routes.

Provides endpoints for retrieving sector and market classification
information for N100 companies.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.database import DB_PATH


# ---------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/sectors",
    tags=["Sectors"],
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
# LIST SECTOR DATA
# ---------------------------------------------------------------------

@router.get("/")
def get_sectors():
    """Return all sectors with company count and median financial metrics."""

    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            WITH latest_ratios AS (
                SELECT
                    fr.company_id,
                    fr.return_on_equity_pct,
                    fr.debt_to_equity
                FROM financial_ratios fr
                INNER JOIN (
                    SELECT
                        company_id,
                        MAX(year) AS latest_year
                    FROM financial_ratios
                    GROUP BY company_id
                ) latest
                    ON fr.company_id = latest.company_id
                    AND fr.year = latest.latest_year
            ),

            latest_market_cap AS (
                SELECT
                    mc.company_id,
                    mc.pe_ratio
                FROM market_cap mc
                INNER JOIN (
                    SELECT
                        company_id,
                        MAX(year) AS latest_year
                    FROM market_cap
                    GROUP BY company_id
                ) latest
                    ON mc.company_id = latest.company_id
                    AND mc.year = latest.latest_year
            ),

            sector_companies AS (
                SELECT DISTINCT
                    company_id,
                    broad_sector
                FROM sectors
            ),

            roe_ranked AS (
                SELECT
                    sc.broad_sector,
                    lr.return_on_equity_pct,
                    ROW_NUMBER() OVER (
                        PARTITION BY sc.broad_sector
                        ORDER BY lr.return_on_equity_pct
                    ) AS rn,
                    COUNT(lr.return_on_equity_pct) OVER (
                        PARTITION BY sc.broad_sector
                    ) AS cnt
                FROM sector_companies sc
                INNER JOIN latest_ratios lr
                    ON sc.company_id = lr.company_id
                WHERE lr.return_on_equity_pct IS NOT NULL
            ),

            pe_ranked AS (
                SELECT
                    sc.broad_sector,
                    lm.pe_ratio,
                    ROW_NUMBER() OVER (
                        PARTITION BY sc.broad_sector
                        ORDER BY lm.pe_ratio
                    ) AS rn,
                    COUNT(lm.pe_ratio) OVER (
                        PARTITION BY sc.broad_sector
                    ) AS cnt
                FROM sector_companies sc
                INNER JOIN latest_market_cap lm
                    ON sc.company_id = lm.company_id
                WHERE lm.pe_ratio IS NOT NULL
            ),

            de_ranked AS (
                SELECT
                    sc.broad_sector,
                    lr.debt_to_equity,
                    ROW_NUMBER() OVER (
                        PARTITION BY sc.broad_sector
                        ORDER BY lr.debt_to_equity
                    ) AS rn,
                    COUNT(lr.debt_to_equity) OVER (
                        PARTITION BY sc.broad_sector
                    ) AS cnt
                FROM sector_companies sc
                INNER JOIN latest_ratios lr
                    ON sc.company_id = lr.company_id
                WHERE lr.debt_to_equity IS NOT NULL
            ),

            roe_median AS (
                SELECT
                    broad_sector,
                    AVG(return_on_equity_pct) AS median_roe
                FROM roe_ranked
                WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
                GROUP BY broad_sector
            ),

            pe_median AS (
                SELECT
                    broad_sector,
                    AVG(pe_ratio) AS median_pe
                FROM pe_ranked
                WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
                GROUP BY broad_sector
            ),

            de_median AS (
                SELECT
                    broad_sector,
                    AVG(debt_to_equity) AS median_de
                FROM de_ranked
                WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
                GROUP BY broad_sector
            )

            SELECT
                sc.broad_sector,
                COUNT(DISTINCT sc.company_id) AS company_count,
                ROUND(rm.median_roe, 2) AS median_roe,
                ROUND(pm.median_pe, 2) AS median_pe,
                ROUND(dm.median_de, 2) AS median_de

            FROM sector_companies sc

            LEFT JOIN roe_median rm
                ON sc.broad_sector = rm.broad_sector

            LEFT JOIN pe_median pm
                ON sc.broad_sector = pm.broad_sector

            LEFT JOIN de_median dm
                ON sc.broad_sector = dm.broad_sector

            GROUP BY
                sc.broad_sector,
                rm.median_roe,
                pm.median_pe,
                dm.median_de

            ORDER BY sc.broad_sector
            """
        ).fetchall()

        sectors = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "count": len(sectors),
        "sectors": sectors,
    }

# ---------------------------------------------------------------------
# GET COMPANIES BY SECTOR
# ---------------------------------------------------------------------

@router.get("/{sector}/companies")
def get_sector_companies(sector: str):
    """Return all companies in a sector with their latest-year KPIs."""

    connection = get_db_connection()

    try:
        # Verify that the sector exists.
        sector_row = connection.execute(
            """
            SELECT DISTINCT broad_sector
            FROM sectors
            WHERE LOWER(broad_sector) = LOWER(?)
            """,
            (sector,),
        ).fetchone()

        if sector_row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Sector '{sector}' not found.",
            )

        actual_sector = sector_row["broad_sector"]

        rows = connection.execute(
            """
            SELECT
                s.company_id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                fr.year,
                fr.return_on_equity_pct,
                fr.return_on_capital_employed_pct,
                fr.net_profit_margin_pct,
                fr.operating_profit_margin_pct,
                fr.debt_to_equity,
                fr.interest_coverage,
                fr.revenue_cagr_5y,
                fr.pat_cagr_5y,
                fr.free_cash_flow_cr,
                fr.composite_quality_score
            FROM sectors s
            JOIN companies c
                ON c.id = s.company_id
            LEFT JOIN financial_ratios fr
                ON fr.company_id = s.company_id
                AND fr.year = (
                    SELECT MAX(fr2.year)
                    FROM financial_ratios fr2
                    WHERE fr2.company_id = s.company_id
                )
            WHERE LOWER(s.broad_sector) = LOWER(?)
            ORDER BY c.company_name
            """,
            (actual_sector,),
        ).fetchall()

        companies = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "sector": actual_sector,
        "count": len(companies),
        "companies": companies,
    }

# ---------------------------------------------------------------------
# GET SINGLE COMPANY SECTOR
# ---------------------------------------------------------------------

@router.get("/{company_id}")
def get_company_sector(company_id: str):
    """Return sector information for a single company."""

    connection = get_db_connection()

    try:
        row = connection.execute(
            """
            SELECT
                company_id,
                broad_sector,
                sub_sector,
                index_weight_pct,
                market_cap_category
            FROM sectors
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchone()

    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sector information for '{company_id}' not found.",
        )

    return dict(row)


# ---------------------------------------------------------------------
# SECTOR SUMMARY
# ---------------------------------------------------------------------

@router.get("/summary/all")
def get_sector_summary():
    """Return company count and index weight by broad sector."""

    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                broad_sector,
                COUNT(*) AS company_count,
                ROUND(SUM(index_weight_pct), 2) AS total_index_weight_pct
            FROM sectors
            GROUP BY broad_sector
            ORDER BY company_count DESC
            """
        ).fetchall()

        summary = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "count": len(summary),
        "sectors": summary,
    }