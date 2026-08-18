"""
Companies API routes.

Provides endpoints for retrieving N100 company information.
"""

import sqlite3
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.database import DB_PATH


# ---------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/companies",
    tags=["Companies"],
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
# LIST COMPANIES
# ---------------------------------------------------------------------

@router.get("/")
def get_companies(
    sector: str | None = Query(default=None),
    market_cap_category: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    """Return all N100 companies with optional filters."""

    connection = get_db_connection()

    try:
        query = """
            SELECT
                c.id AS company_id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                c.roe_percentage AS roe_pct,
                c.roce_percentage AS roce_pct
            FROM companies c
            LEFT JOIN sectors s
                ON c.id = s.company_id
            WHERE 1 = 1
        """

        params = []

        if sector:
            query += " AND s.broad_sector = ?"
            params.append(sector)

        if market_cap_category:
            query += " AND s.market_cap_category = ?"
            params.append(market_cap_category)

        if search:
            query += """
                AND (
                    c.id LIKE ?
                    OR c.company_name LIKE ?
                )
            """
            search_value = f"%{search}%"
            params.extend([search_value, search_value])

        query += " ORDER BY c.company_name"

        rows = connection.execute(
            query,
            params,
        ).fetchall()

        companies = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "count": len(companies),
        "companies": companies,
    }


# ---------------------------------------------------------------------
# GET SINGLE COMPANY
# ---------------------------------------------------------------------

@router.get("/{company_id}")
def get_company(company_id: str):
    """Return details for a single company."""

    connection = get_db_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id AS company_id,
                company_name,
                company_logo,
                chart_link,
                about_company,
                website,
                nse_profile,
                bse_profile,
                face_value,
                book_value,
                roce_percentage,
                roe_percentage
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

    finally:
        connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{company_id}' not found.",
        )

    return dict(row)


# ---------------------------------------------------------------------
# P&L HISTORY
# ---------------------------------------------------------------------

@router.get("/{company_id}/pl")
def get_profit_and_loss(
    company_id: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return profit and loss history for a company."""

    connection = get_db_connection()

    try:
        company_exists = connection.execute(
            "SELECT 1 FROM companies WHERE id = ?",
            (company_id,),
        ).fetchone()

        if company_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found.",
            )

        query = """
            SELECT
                year,
                sales,
                expenses,
                operating_profit,
                opm_percentage,
                other_income,
                interest,
                depreciation,
                profit_before_tax,
                tax_percentage,
                net_profit,
                eps,
                dividend_payout
            FROM profitandloss
            WHERE company_id = ?
        """

        params = [company_id]

        if from_year:
            query += " AND year >= ?"
            params.append(int(from_year[:4]))

        if to_year:
            query += " AND year <= ?"
            params.append(int(to_year[:4]))

        query += " ORDER BY year"

        rows = connection.execute(
            query,
            params,
        ).fetchall()

        history = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "company_id": company_id,
        "count": len(history),
        "history": history,
    }


# ---------------------------------------------------------------------
# BALANCE SHEET HISTORY
# ---------------------------------------------------------------------

@router.get("/{company_id}/bs")
def get_balance_sheet(
    company_id: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return balance sheet history for a company."""

    connection = get_db_connection()

    try:
        company_exists = connection.execute(
            "SELECT 1 FROM companies WHERE id = ?",
            (company_id,),
        ).fetchone()

        if company_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found.",
            )

        query = """
            SELECT
                year,
                equity_capital,
                reserves,
                borrowings,
                other_liabilities,
                total_liabilities,
                fixed_assets,
                cwip,
                investments,
                other_asset,
                total_assets
            FROM balancesheet
            WHERE company_id = ?
        """

        params = [company_id]

        if from_year:
            query += " AND year >= ?"
            params.append(int(from_year[:4]))

        if to_year:
            query += " AND year <= ?"
            params.append(int(to_year[:4]))

        query += " ORDER BY year"

        rows = connection.execute(
            query,
            params,
        ).fetchall()

        history = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "company_id": company_id,
        "count": len(history),
        "history": history,
    }


# ---------------------------------------------------------------------
# CASH FLOW HISTORY
# ---------------------------------------------------------------------

@router.get("/{company_id}/cashflow")
def get_cash_flow(
    company_id: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return cash flow history for a company."""

    connection = get_db_connection()

    try:
        company_exists = connection.execute(
            "SELECT 1 FROM companies WHERE id = ?",
            (company_id,),
        ).fetchone()

        if company_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found.",
            )

        query = """
            SELECT
                year,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
            WHERE company_id = ?
        """

        params = [company_id]

        if from_year:
            query += " AND year >= ?"
            params.append(int(from_year[:4]))

        if to_year:
            query += " AND year <= ?"
            params.append(int(to_year[:4]))

        query += " ORDER BY year"

        rows = connection.execute(
            query,
            params,
        ).fetchall()

        history = [dict(row) for row in rows]

    finally:
        connection.close()

    return {
        "company_id": company_id,
        "count": len(history),
        "history": history,
    }

# ---------------------------------------------------------------------
# GET COMPANY FINANCIAL RATIOS
# ---------------------------------------------------------------------

@router.get("/{company_id}/ratios")
def get_company_ratios(
    company_id: str,
    year: int | None = None,
):
    """
    Return computed financial ratios for a company.

    If year is provided, return ratios for that year only.
    Otherwise, return the complete available ratio history.
    """

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
            (company_id.upper(),),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id.upper()}' not found.",
            )

        # -------------------------------------------------------------
        # GET RATIOS
        # -------------------------------------------------------------

        query = """
            SELECT
                company_id,
                year,
                net_profit_margin_pct,
                operating_profit_margin_pct,
                return_on_equity_pct,
                return_on_capital_employed_pct,
                return_on_assets_pct,
                debt_to_equity,
                interest_coverage,
                net_debt_cr,
                asset_turnover,
                earnings_per_share,
                book_value_per_share,
                dividend_payout_ratio_pct,
                total_debt_cr,
                cash_from_operations_cr,
                free_cash_flow_cr,
                capex_intensity_pct,
                capex_intensity_label,
                fcf_conversion_pct,
                capital_allocation_pattern,
                revenue_cagr_5y,
                pat_cagr_5y,
                eps_cagr_5y,
                composite_quality_score,
                capex_cr
            FROM financial_ratios
            WHERE company_id = ?
        """

        parameters = [company["company_id"]]

        if year is not None:
            query += " AND year = ?"
            parameters.append(year)

        query += " ORDER BY year DESC"

        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

        ratios = [dict(row) for row in rows]

    finally:
        connection.close()

    # -------------------------------------------------------------
    # NO DATA
    # -------------------------------------------------------------

    if not ratios:
        if year is not None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No financial ratios found for "
                    f"'{company_id.upper()}' in {year}."
                ),
            )

        raise HTTPException(
            status_code=404,
            detail=(
                f"No financial ratios found for "
                f"'{company_id.upper()}'."
            ),
        )

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "year": year,
        "count": len(ratios),
        "ratios": ratios,
    }

# ---------------------------------------------------------------------
# GET COMPANY TEARSHEET
# ---------------------------------------------------------------------

@router.get("/{company_id}/tearsheet")
def get_company_tearsheet(company_id: str):
    """Return the company's pre-generated tearsheet PDF."""

    company_id = company_id.upper()

    # Verify company exists
    connection = get_db_connection()

    try:
        company = connection.execute(
            """
            SELECT id
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (company_id,),
        ).fetchone()
    finally:
        connection.close()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{company_id}' not found.",
        )

    # Project root:
    # companies.py -> routers -> api -> src -> project root
    project_root = Path(__file__).resolve().parents[3]

    tearsheet_path = (
        project_root
        / "reports"
        / "tearsheets"
        / f"{company_id}_tearsheet.pdf"
    )

    if not tearsheet_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet for company '{company_id}' not found.",
        )

    return FileResponse(
        path=str(tearsheet_path),
        media_type="application/pdf",
        filename=f"{company_id}_tearsheet.pdf",
    )

# ---------------------------------------------------------------------
# PEER COMPARISON
# ---------------------------------------------------------------------

@router.get("/{company_id}/peers/compare")
def compare_company_peers(company_id: str):
    """Return peer comparison metrics for a company."""

    company_id = company_id.upper()

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

        peer_group = connection.execute(
            """
            SELECT peer_group_name
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
                COALESCE(pg.is_benchmark, 0) AS is_benchmark
            FROM peer_percentiles pp
            LEFT JOIN companies c
                ON c.id = pp.company_id
            LEFT JOIN peer_groups pg
                ON pg.company_id = pp.company_id
               AND pg.peer_group_name = pp.peer_group_name
            WHERE pp.peer_group_name = ?
            ORDER BY pp.metric, pp.percentile_rank DESC, pp.company_id, pp.year
            """,
            (peer_group["peer_group_name"],),
        ).fetchall()

        comparison = [dict(row) for row in rows]

    finally:
        connection.close()

    if not comparison:
        raise HTTPException(
            status_code=404,
            detail=f"No peer comparison data found for '{company_id}'.",
        )

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "peer_group_name": peer_group["peer_group_name"],
        "count": len(comparison),
        "comparison": comparison,
    }