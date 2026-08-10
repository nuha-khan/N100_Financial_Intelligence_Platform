import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_sectors,
    _read_query,
)


# ==================================================================
# PAGE CONFIGURATION
# ==================================================================

st.set_page_config(
    page_title="Capital Allocation | Nifty 100 Analytics",
    layout="wide",
)


# ==================================================================
# CONSTANTS
# ==================================================================

DB_MARKET_CAP_TABLE = "market_cap"

CAPITAL_COLUMNS = [
    "company_id",
    "company_name",
    "broad_sector",
    "market_cap_crore",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "free_cash_flow_cr",
    "debt_to_equity",
]


# ==================================================================
# HELPERS
# ==================================================================

@st.cache_data(ttl=600)
def get_market_cap_data(year=None):
    """
    Return market-cap and valuation data for the official
    92-company universe.

    The companies table is used as the master universe so
    supporting datasets cannot expand the dashboard universe.
    """

    if year is None:

        query = """
            WITH latest_year AS (
                SELECT MAX(year) AS year
                FROM market_cap
            )

            SELECT
                c.id AS company_id,
                c.company_name,

                s.broad_sector,

                mc.year,
                mc.market_cap_crore,
                mc.pe_ratio,
                mc.pb_ratio,
                mc.dividend_yield_pct

            FROM companies c

            LEFT JOIN latest_year ly
                ON 1 = 1

            LEFT JOIN market_cap mc
                ON c.id = mc.company_id
                AND mc.year = ly.year

            LEFT JOIN sectors s
                ON c.id = s.company_id

            ORDER BY
                mc.market_cap_crore DESC,
                c.company_name
        """

        return _read_query(query)

    query = """
        SELECT
            c.id AS company_id,
            c.company_name,

            s.broad_sector,

            mc.year,
            mc.market_cap_crore,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.dividend_yield_pct

        FROM companies c

        LEFT JOIN market_cap mc
            ON c.id = mc.company_id
            AND mc.year = ?

        LEFT JOIN sectors s
            ON c.id = s.company_id

        ORDER BY
            mc.market_cap_crore DESC,
            c.company_name
    """

    return _read_query(
        query,
        [year],
    )


@st.cache_data(ttl=600)
def get_available_market_cap_years():
    """
    Return all financial years available in market_cap.
    """

    query = """
        SELECT DISTINCT year
        FROM market_cap
        WHERE year IS NOT NULL
        ORDER BY year
    """

    df = _read_query(query)

    if df.empty:
        return []

    return (
        pd.to_numeric(
            df["year"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .tolist()
    )


def get_latest_ratio_row(ticker, year):
    """
    Return the ratio record for a company and selected year.
    """

    ratios = get_ratios(
        ticker,
        year=year,
    )

    if ratios.empty:
        return None

    return ratios.iloc[-1]


def add_ratio_metrics(market_df, year):
    """
    Add already-calculated financial ratio metrics to the
    market-cap dataset.

    No ratio calculations are performed here.
    """

    if market_df.empty:
        return market_df

    records = []

    for _, row in market_df.iterrows():

        ticker = row["company_id"]

        ratio_row = get_latest_ratio_row(
            ticker,
            year,
        )

        if ratio_row is None:
            records.append(
                {
                    "company_id": ticker,
                    "return_on_equity_pct": None,
                    "return_on_capital_employed_pct": None,
                    "free_cash_flow_cr": None,
                    "debt_to_equity": None,
                }
            )

            continue

        records.append(
            {
                "company_id": ticker,

                "return_on_equity_pct":
                    ratio_row.get(
                        "return_on_equity_pct"
                    ),

                "return_on_capital_employed_pct":
                    ratio_row.get(
                        "return_on_capital_employed_pct"
                    ),

                "free_cash_flow_cr":
                    ratio_row.get(
                        "free_cash_flow_cr"
                    ),

                "debt_to_equity":
                    ratio_row.get(
                        "debt_to_equity"
                    ),
            }
        )

    ratios_df = pd.DataFrame(records)

    return market_df.merge(
        ratios_df,
        on="company_id",
        how="left",
    )


def clean_numeric_columns(df):
    """
    Convert numeric columns safely.
    """

    numeric_columns = [
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "free_cash_flow_cr",
        "debt_to_equity",
    ]

    result = df.copy()

    for column in numeric_columns:

        if column in result.columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result


def format_crore(value):
    """
    Format crore values into readable Indian financial units.
    """

    if pd.isna(value):
        return "N/A"

    value = float(value)

    if value >= 100000:
        return f"₹{value / 100000:.2f} L Cr"

    if value >= 1000:
        return f"₹{value / 1000:.2f} K Cr"

    return f"₹{value:.2f} Cr"


# ==================================================================
# PAGE HEADER
# ==================================================================

st.title("💰 Capital Allocation")

st.caption(
    "Analyse market capitalization, valuation, shareholder returns "
    "and capital efficiency across the official Nifty 100 universe."
)


# ==================================================================
# LOAD COMPANY UNIVERSE
# ==================================================================

companies = get_companies()

if companies.empty:

    st.warning(
        "Company master data is unavailable."
    )

    st.stop()


official_company_count = (
    companies["id"]
    .dropna()
    .nunique()
)


# ==================================================================
# YEAR SELECTOR
# ==================================================================

available_years = get_available_market_cap_years()

if not available_years:

    st.warning(
        "No market-capitalization data is available."
    )

    st.stop()


selected_year = st.selectbox(
    "Financial Year",
    available_years,
    index=len(available_years) - 1,
)


# ==================================================================
# LOAD MARKET DATA
# ==================================================================

capital_df = get_market_cap_data(
    selected_year
)

if capital_df.empty:

    st.warning(
        f"No capital-market data is available for {selected_year}."
    )

    st.stop()


capital_df = clean_numeric_columns(
    capital_df
)


# Add calculated/validated ratio data
capital_df = add_ratio_metrics(
    capital_df,
    selected_year,
)


capital_df = clean_numeric_columns(
    capital_df
)


# ==================================================================
# DATA QUALITY / UNIVERSE CHECK
# ==================================================================

st.caption(
    f"Capital analytics based on the official "
    f"{official_company_count}-company universe for {selected_year}."
)


# ==================================================================
# KPI SECTION
# ==================================================================

st.subheader("Capital Market Overview")


total_market_cap = capital_df[
    "market_cap_crore"
].sum(
    skipna=True
)


median_pe = capital_df[
    "pe_ratio"
].median(
    skipna=True
)


median_pb = capital_df[
    "pb_ratio"
].median(
    skipna=True
)


average_dividend_yield = capital_df[
    "dividend_yield_pct"
].mean(
    skipna=True
)


kpi_columns = st.columns(4)


with kpi_columns[0]:

    st.metric(
        "Total Market Cap",
        format_crore(
            total_market_cap
        ),
    )


with kpi_columns[1]:

    if pd.isna(median_pe):

        st.metric(
            "Median P/E",
            "N/A",
        )

    else:

        st.metric(
            "Median P/E",
            f"{median_pe:.2f}",
        )


with kpi_columns[2]:

    if pd.isna(median_pb):

        st.metric(
            "Median P/B",
            "N/A",
        )

    else:

        st.metric(
            "Median P/B",
            f"{median_pb:.2f}",
        )


with kpi_columns[3]:

    if pd.isna(average_dividend_yield):

        st.metric(
            "Average Dividend Yield",
            "N/A",
        )

    else:

        st.metric(
            "Average Dividend Yield",
            f"{average_dividend_yield:.2f}%",
        )


# ==================================================================
# MARKET CAP RANKING
# ==================================================================

st.subheader("📊 Market Capitalization Ranking")

ranking_df = capital_df[
    [
        "company_id",
        "company_name",
        "market_cap_crore",
    ]
].dropna(
    subset=["market_cap_crore"]
).sort_values(
    "market_cap_crore",
    ascending=False,
)


top_n = st.slider(
    "Number of companies",
    min_value=5,
    max_value=20,
    value=10,
)


top_market_cap = ranking_df.head(
    top_n
).copy()


top_market_cap = top_market_cap.sort_values(
    "market_cap_crore"
)


if not top_market_cap.empty:

    figure = px.bar(
        top_market_cap,
        x="market_cap_crore",
        y="company_name",
        orientation="h",
        title=f"Top {top_n} Companies by Market Capitalization",
        labels={
            "market_cap_crore": "Market Cap (₹ Cr)",
            "company_name": "Company",
        },
        hover_data={
            "company_id": True,
            "market_cap_crore": ":,.2f",
        },
    )

    figure.update_layout(
        height=max(
            450,
            top_n * 35,
        ),
        margin=dict(
            l=20,
            r=30,
            t=70,
            b=40,
        ),
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )


# ==================================================================
# SECTOR CAPITAL CONCENTRATION
# ==================================================================

st.subheader("🏢 Market Capitalization by Sector")

sector_market_cap = (
    capital_df
    .dropna(
        subset=[
            "broad_sector",
            "market_cap_crore",
        ]
    )
    .groupby(
        "broad_sector",
        as_index=False,
    )["market_cap_crore"]
    .sum()
    .sort_values(
        "market_cap_crore",
        ascending=False,
    )
)


if not sector_market_cap.empty:

    sector_figure = px.bar(
        sector_market_cap,
        x="broad_sector",
        y="market_cap_crore",
        title="Market Capitalization Concentration by Sector",
        labels={
            "broad_sector": "Sector",
            "market_cap_crore": "Market Cap (₹ Cr)",
        },
    )

    sector_figure.update_layout(
        xaxis_tickangle=-35,
        height=500,
        margin=dict(
            l=40,
            r=30,
            t=70,
            b=120,
        ),
    )

    st.plotly_chart(
        sector_figure,
        use_container_width=True,
    )


# ==================================================================
# CAPITAL ALLOCATION MATRIX
# ==================================================================

st.subheader("🎯 Capital Allocation Matrix")

st.caption(
    "Companies are positioned using return on equity and free "
    "cash flow. Bubble size represents market capitalization."
)


matrix_df = capital_df[
    [
        "company_id",
        "company_name",
        "broad_sector",
        "market_cap_crore",
        "return_on_equity_pct",
        "free_cash_flow_cr",
        "dividend_yield_pct",
        "debt_to_equity",
    ]
].copy()


matrix_df = matrix_df.dropna(
    subset=[
        "return_on_equity_pct",
        "free_cash_flow_cr",
        "market_cap_crore",
    ]
)


if not matrix_df.empty:

    matrix_figure = px.scatter(
        matrix_df,
        x="return_on_equity_pct",
        y="free_cash_flow_cr",
        size="market_cap_crore",
        color="broad_sector",
        hover_name="company_name",
        hover_data={
            "company_id": True,
            "return_on_equity_pct": ":.2f",
            "free_cash_flow_cr": ":,.2f",
            "market_cap_crore": ":,.2f",
            "dividend_yield_pct": ":.2f",
            "debt_to_equity": ":.2f",
        },
        title=(
            "Return on Equity vs Free Cash Flow"
        ),
        labels={
            "return_on_equity_pct": "ROE (%)",
            "free_cash_flow_cr": "Free Cash Flow (₹ Cr)",
            "broad_sector": "Sector",
        },
    )

    matrix_figure.update_layout(
        height=600,
        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50,
        ),
    )

    st.plotly_chart(
        matrix_figure,
        use_container_width=True,
    )

else:

    st.info(
        "Insufficient ROE, free-cash-flow and market-cap data "
        "to construct the capital allocation matrix."
    )


# ==================================================================
# VALUATION COMPARISON
# ==================================================================

st.subheader("📈 Valuation Overview")

valuation_df = capital_df[
    [
        "company_id",
        "company_name",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
    ]
].copy()


valuation_df = valuation_df.dropna(
    subset=[
        "pe_ratio",
        "pb_ratio",
    ]
)


if not valuation_df.empty:

    valuation_figure = px.scatter(
        valuation_df,
        x="pe_ratio",
        y="pb_ratio",
        size="market_cap_crore",
        hover_name="company_name",
        hover_data={
            "company_id": True,
            "pe_ratio": ":.2f",
            "pb_ratio": ":.2f",
            "dividend_yield_pct": ":.2f",
            "market_cap_crore": ":,.2f",
        },
        title="P/E vs P/B Valuation Map",
        labels={
            "pe_ratio": "P/E Ratio",
            "pb_ratio": "P/B Ratio",
        },
    )

    valuation_figure.update_layout(
        height=550,
        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50,
        ),
    )

    st.plotly_chart(
        valuation_figure,
        use_container_width=True,
    )

else:

    st.info(
        "Valuation data is insufficient to construct "
        "the P/E vs P/B comparison."
    )


# ==================================================================
# DIVIDEND YIELD ANALYSIS
# ==================================================================

st.subheader("💵 Dividend Yield")

dividend_df = capital_df[
    [
        "company_id",
        "company_name",
        "dividend_yield_pct",
    ]
].dropna(
    subset=[
        "dividend_yield_pct",
    ]
).sort_values(
    "dividend_yield_pct",
    ascending=False,
)


if not dividend_df.empty:

    dividend_top = dividend_df.head(
        15
    ).sort_values(
        "dividend_yield_pct"
    )

    dividend_figure = px.bar(
        dividend_top,
        x="dividend_yield_pct",
        y="company_name",
        orientation="h",
        title="Top Companies by Dividend Yield",
        labels={
            "dividend_yield_pct": "Dividend Yield (%)",
            "company_name": "Company",
        },
        hover_data={
            "company_id": True,
            "dividend_yield_pct": ":.2f",
        },
    )

    dividend_figure.update_layout(
        height=550,
        margin=dict(
            l=20,
            r=30,
            t=70,
            b=40,
        ),
    )

    st.plotly_chart(
        dividend_figure,
        use_container_width=True,
    )

else:

    st.info(
        "Dividend-yield data is unavailable."
    )


# ==================================================================
# CAPITAL ALLOCATION TABLE
# ==================================================================

st.subheader("📋 Capital Allocation Overview")


display_df = capital_df[
    [
        "company_id",
        "company_name",
        "broad_sector",
        "market_cap_crore",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "free_cash_flow_cr",
        "debt_to_equity",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
    ]
].copy()


display_df = display_df.sort_values(
    "market_cap_crore",
    ascending=False,
)


display_df = display_df.rename(
    columns={
        "company_id": "Company ID",
        "company_name": "Company Name",
        "broad_sector": "Sector",
        "market_cap_crore": "Market Cap (₹ Cr)",
        "return_on_equity_pct": "ROE (%)",
        "return_on_capital_employed_pct": "ROCE (%)",
        "free_cash_flow_cr": "Free Cash Flow (₹ Cr)",
        "debt_to_equity": "D/E",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Dividend Yield (%)",
    }
)


numeric_display_columns = [
    "Market Cap (₹ Cr)",
    "ROE (%)",
    "ROCE (%)",
    "Free Cash Flow (₹ Cr)",
    "D/E",
    "P/E",
    "P/B",
    "Dividend Yield (%)",
]


for column in numeric_display_columns:

    display_df[column] = pd.to_numeric(
        display_df[column],
        errors="coerce",
    ).round(2)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# ==================================================================
# DATA AVAILABILITY NOTE
# ==================================================================

missing_columns = []

for column in [
    "market_cap_crore",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "return_on_equity_pct",
    "free_cash_flow_cr",
]:

    if capital_df[column].isna().all():

        missing_columns.append(
            column
        )


if missing_columns:

    st.caption(
        "N/A values indicate that the corresponding metric "
        "is unavailable in the underlying validated datasets."
    )


# ==================================================================
# FOOTER
# ==================================================================

st.caption(
    "Capital-market metrics are sourced from the validated "
    "Nifty 100 database. Financial-ratio values shown here "
    "reuse the Sprint 4 ratio engine outputs."
)