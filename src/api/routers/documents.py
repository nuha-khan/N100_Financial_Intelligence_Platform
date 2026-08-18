"""
Documents API routes.

Provides endpoints for retrieving annual report information
for N100 companies.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.database import DB_PATH


# ---------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
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
# GET ALL REPORTS FOR A COMPANY
# ---------------------------------------------------------------------

@router.get("/{company_id}")
def get_company_documents(company_id: str):
    """Return all annual reports available for a company."""

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
                Year AS year,
                Annual_Report AS annual_report
            FROM documents
            WHERE company_id = ?
            ORDER BY Year DESC
            """,
            (company_id,),
        ).fetchall()

        reports = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "count": len(reports),
        "documents": reports,
    }

# ---------------------------------------------------------------------
# GET LATEST REPORT
# ---------------------------------------------------------------------

@router.get("/{company_id}/latest")
def get_latest_company_document(company_id: str):
    """Return the latest annual report available for a company."""

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

        row = connection.execute(
            """
            SELECT
                Year AS year,
                Annual_Report AS annual_report
            FROM documents
            WHERE company_id = ?
            ORDER BY Year DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No annual reports found for '{company_id}'.",
        )

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "document": dict(row),
    }

# ---------------------------------------------------------------------
# GET SPECIFIC YEAR REPORT
# ---------------------------------------------------------------------

@router.get("/{company_id}/{year}")
def get_company_document(company_id: str, year: int):
    """Return the annual report for a specific company and year."""

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

        row = connection.execute(
            """
            SELECT
                Year AS year,
                Annual_Report AS annual_report
            FROM documents
            WHERE company_id = ?
              AND Year = ?
            LIMIT 1
            """,
            (company_id, year),
        ).fetchone()

    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No annual report found for "
                f"'{company_id}' in {year}."
            ),
        )

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "document": dict(row),
    }