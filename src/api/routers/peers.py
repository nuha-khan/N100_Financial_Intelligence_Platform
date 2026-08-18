"""
Peer Intelligence API routes.

Provides endpoints for retrieving peer groups and
peer comparison information for N100 companies.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.database import DB_PATH


# ---------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/peers",
    tags=["Peers"],
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
# GET PEER GROUPS
# ---------------------------------------------------------------------

@router.get("/")
def get_peer_groups():
    """Return all peer groups."""

    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM peer_groups
            ORDER BY company_id
            """
        ).fetchall()

        peer_groups = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "count": len(peer_groups),
        "peer_groups": peer_groups,
    }

# ---------------------------------------------------------------------
# GET COMPANIES BY PEER GROUP
# ---------------------------------------------------------------------

@router.get("/group/{group_name}")
def get_peer_group(group_name: str):
    """Return all companies belonging to a specific peer group."""

    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                pg.peer_group_name,
                pg.company_id,
                c.company_name,
                pg.is_benchmark
            FROM peer_groups AS pg
            LEFT JOIN companies AS c
                ON c.id = pg.company_id
            WHERE LOWER(pg.peer_group_name) = LOWER(?)
            ORDER BY pg.is_benchmark DESC, pg.company_id
            """,
            (group_name,),
        ).fetchall()

        peers = [dict(row) for row in rows]

    finally:
        connection.close()

    if not peers:
        raise HTTPException(
            status_code=404,
            detail=f"Peer group '{group_name}' not found.",
        )

    return {
        "peer_group_name": group_name,
        "count": len(peers),
        "companies": peers,
    }

# ---------------------------------------------------------------------
# GET PEERS FOR COMPANY
# ---------------------------------------------------------------------

@router.get("/{company_id}")
def get_company_peers(company_id: str):
    """Return peer information for a specific company."""

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
            SELECT *
            FROM peer_groups
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchall()

        peers = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "company_id": company_id,
        "company_name": company["company_name"],
        "peer_count": len(peers),
        "peers": peers,
    }


# ---------------------------------------------------------------------
# GET PEER PERCENTILES
# ---------------------------------------------------------------------

@router.get("/{company_id}/percentiles")
def get_peer_percentiles(company_id: str):
    """Return peer percentile information for a company."""

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
            SELECT *
            FROM peer_percentiles
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchall()

        percentiles = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "company_id": company_id,
        "company_name": company["company_name"],
        "percentiles": percentiles,
    }

# ---------------------------------------------------------------------
# PEER COMPARISON
# ---------------------------------------------------------------------

@router.get("/{company_id}/compare")
def compare_company_with_peers(company_id: str):
    """Return peer comparison metrics for a company."""

    company_id = company_id.upper()

    connection = get_db_connection()

    try:
        # -------------------------------------------------------------
        # VERIFY COMPANY
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # GET PEER GROUP
        # -------------------------------------------------------------

        peer_group = connection.execute(
            """
            SELECT
                peer_group_name,
                is_benchmark
            FROM peer_groups
            WHERE company_id = ?
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

        if peer_group is None:
            raise HTTPException(
                status_code=404,
                detail=f"No peer group found for '{company_id}'.",
            )

        # -------------------------------------------------------------
        # GET PEER COMPARISON DATA
        # -------------------------------------------------------------

        rows = connection.execute(
            """
            SELECT
                pp.company_id,
                c.company_name,
                pp.peer_group_name,
                pp.metric,
                pp.value,
                pp.percentile_rank,
                pp.year,
                pg.is_benchmark
            FROM peer_percentiles AS pp
            LEFT JOIN companies AS c
                ON c.id = pp.company_id
            LEFT JOIN peer_groups AS pg
                ON pg.company_id = pp.company_id
               AND pg.peer_group_name = pp.peer_group_name
            WHERE pp.peer_group_name = ?
            ORDER BY pp.metric, pp.percentile_rank DESC, pp.company_id
            """,
            (peer_group["peer_group_name"],),
        ).fetchall()

        comparison = [dict(row) for row in rows]

    finally:
        connection.close()

    if not comparison:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No peer comparison data found for "
                f"'{company_id}'."
            ),
        )

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "peer_group_name": peer_group["peer_group_name"],
        "count": len(comparison),
        "comparison": comparison,
    }