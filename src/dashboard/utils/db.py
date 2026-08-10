import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# ------------------------------------------------------------------
# Database Configuration
# ------------------------------------------------------------------

DB_PATH = Path("data/nifty100.db")


# ------------------------------------------------------------------
# Generic Database Helper
# ------------------------------------------------------------------

def _read_query(query, params=None):
    """
    Execute a SQLite query and return the result as a DataFrame.

    A fresh connection is created for each query and always closed
    after execution.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)

    try:
        return pd.read_sql_query(
            query,
            conn,
            params=params,
        )

    finally:
        conn.close()


# ------------------------------------------------------------------
# Company Master Data
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_companies():
    """
    Return all company master records.
    """

    return _read_query(
        """
        SELECT *
        FROM companies
        ORDER BY company_name
        """
    )


# ------------------------------------------------------------------
# Financial Ratios
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Return financial ratios for a company.

    Parameters
    ----------
    ticker : str
        Company ID / ticker.

    year : optional
        If supplied, only that financial year is returned.
    """

    if not ticker:
        return pd.DataFrame()

    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
    """

    params = [ticker]

    if year is not None:

        query += """
            AND year = ?
        """

        params.append(year)

    query += """
        ORDER BY year
    """

    return _read_query(
        query,
        params,
    )


# ------------------------------------------------------------------
# Profit & Loss
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_pl(ticker):
    """
    Return profit and loss history for a company.
    """

    if not ticker:
        return pd.DataFrame()

    return _read_query(
        """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
        """,
        [ticker],
    )


# ------------------------------------------------------------------
# Balance Sheet
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_bs(ticker):
    """
    Return balance sheet history for a company.
    """

    if not ticker:
        return pd.DataFrame()

    return _read_query(
        """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
        """,
        [ticker],
    )


# ------------------------------------------------------------------
# Cash Flow
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_cf(ticker):
    """
    Return cash flow history for a company.
    """

    if not ticker:
        return pd.DataFrame()

    return _read_query(
        """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
        """,
        [ticker],
    )


# ------------------------------------------------------------------
# Sector Data
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_sectors():
    """
    Return sector information for all companies.
    """

    return _read_query(
        """
        SELECT *
        FROM sectors
        """
    )


# ------------------------------------------------------------------
# Peer Groups
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_peers(group_name):
    """
    Return companies belonging to a specific peer group.
    """

    if not group_name:
        return pd.DataFrame()

    return _read_query(
        """
        SELECT *
        FROM peer_groups
        WHERE peer_group_name = ?
        ORDER BY company_id
        """,
        [group_name],
    )


# ------------------------------------------------------------------
# Pros & Cons
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    """
    Return pros and cons for a company.
    """

    if not ticker:
        return pd.DataFrame()

    return _read_query(
        """
        SELECT
            company_id,
            pros,
            cons
        FROM prosandcons
        WHERE company_id = ?
        """,
        [ticker],
    )


# ------------------------------------------------------------------
# Valuation
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Return valuation information for a company.

    The valuation table is not yet present in the current database.
    Valuation will be generated by src/analytics/valuation.py during
    Day 26.

    Until then, return an empty DataFrame instead of raising an error.
    """

    if not ticker:
        return pd.DataFrame()

    # Valuation is generated later in Sprint 4.
    return pd.DataFrame()


# ------------------------------------------------------------------
# Optional Utility: Clear Cached Dashboard Data
# ------------------------------------------------------------------

def clear_dashboard_cache():
    """
    Clear all Streamlit cached database results.
    """

    st.cache_data.clear()

# ------------------------------------------------------------------
# Screener Data
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_screener_data(year=None):
    """
    Return screener data for the official 92-company universe.

    The companies table is used as the master universe so that
    supporting datasets containing additional companies do not
    expand the Nifty 100 screener beyond the 92 official companies.

    Missing financial or market data is retained as NULL/NaN.
    """

    if year is None:

        query = """
            WITH latest_year AS (
                SELECT MAX(year) AS year
                FROM financial_ratios
            )

            SELECT
                c.id AS company_id,
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
                fr.free_cash_flow_cr,
                fr.revenue_cagr_5y,
                fr.pat_cagr_5y,
                fr.eps_cagr_5y,
                fr.composite_quality_score,

                mc.market_cap_crore,
                mc.pe_ratio,
                mc.pb_ratio,
                mc.dividend_yield_pct

            FROM companies c

            LEFT JOIN latest_year ly
                ON 1 = 1

            LEFT JOIN financial_ratios fr
                ON c.id = fr.company_id
                AND fr.year = ly.year

            LEFT JOIN sectors s
                ON c.id = s.company_id

            LEFT JOIN market_cap mc
                ON c.id = mc.company_id
                AND mc.year = ly.year

            ORDER BY
                fr.composite_quality_score DESC,
                c.company_name
        """

        return _read_query(query)

    # --------------------------------------------------------------
    # Specific Financial Year
    # --------------------------------------------------------------

    query = """
        SELECT
            c.id AS company_id,
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
            fr.free_cash_flow_cr,
            fr.revenue_cagr_5y,
            fr.pat_cagr_5y,
            fr.eps_cagr_5y,
            fr.composite_quality_score,

            mc.market_cap_crore,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.dividend_yield_pct

        FROM companies c

        LEFT JOIN financial_ratios fr
            ON c.id = fr.company_id
            AND fr.year = ?

        LEFT JOIN sectors s
            ON c.id = s.company_id

        LEFT JOIN market_cap mc
            ON c.id = mc.company_id
            AND mc.year = ?

        ORDER BY
            fr.composite_quality_score DESC,
            c.company_name
    """

    return _read_query(
        query,
        [year, year],
    )