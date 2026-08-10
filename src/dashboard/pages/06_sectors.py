import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import _read_query


# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Sector Analysis | Nifty 100 Analytics",
    layout="wide",
)


# ------------------------------------------------------------------
# Database Query
# ------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_sector_data():
    """
    Return validated sector-level company analytics.

    The companies table defines the official 92-company universe.
    Supporting datasets cannot expand the universe.
    """

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

        LEFT JOIN sectors s
            ON c.id = s.company_id

        LEFT JOIN latest_year ly
            ON 1 = 1

        LEFT JOIN financial_ratios fr
            ON c.id = fr.company_id
            AND fr.year = ly.year

        LEFT JOIN market_cap mc
            ON c.id = mc.company_id
            AND mc.year = ly.year

        ORDER BY
            s.broad_sector,
            fr.composite_quality_score DESC,
            c.company_name
    """

    return _read_query(query)


# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------

def numeric_columns(df):
    """
    Convert known analytical columns to numeric.
    """

    columns = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "free_cash_flow_cr",
        "revenue_cagr_5y",
        "pat_cagr_5y",
        "eps_cagr_5y",
        "composite_quality_score",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
    ]

    result = df.copy()

    for column in columns:

        if column in result.columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result


def build_sector_summary(df):
    """
    Aggregate company-level analytics into sector-level metrics.
    """

    if df.empty:
        return pd.DataFrame()

    summary = (
        df.groupby("broad_sector", dropna=False)
        .agg(
            companies=("company_id", "nunique"),

            market_cap_crore=(
                "market_cap_crore",
                "sum",
            ),

            avg_quality_score=(
                "composite_quality_score",
                "mean",
            ),

            avg_roe=(
                "return_on_equity_pct",
                "mean",
            ),

            avg_roce=(
                "return_on_capital_employed_pct",
                "mean",
            ),

            avg_npm=(
                "net_profit_margin_pct",
                "mean",
            ),

            avg_opm=(
                "operating_profit_margin_pct",
                "mean",
            ),

            avg_de=(
                "debt_to_equity",
                "mean",
            ),

            avg_interest_coverage=(
                "interest_coverage",
                "mean",
            ),

            avg_revenue_cagr=(
                "revenue_cagr_5y",
                "mean",
            ),

            avg_pat_cagr=(
                "pat_cagr_5y",
                "mean",
            ),

            avg_eps_cagr=(
                "eps_cagr_5y",
                "mean",
            ),

            total_fcf=(
                "free_cash_flow_cr",
                "sum",
            ),
        )
        .reset_index()
    )

    summary["broad_sector"] = (
        summary["broad_sector"]
        .fillna("Unknown")
    )

    return summary


def format_sector_table(df):
    """
    Prepare sector summary for Streamlit display.
    """

    result = df.copy()

    result = result.rename(
        columns={
            "broad_sector": "Sector",
            "companies": "Companies",
            "market_cap_crore": "Market Cap (₹ Cr)",
            "avg_quality_score": "Avg Quality Score",
            "avg_roe": "Avg ROE (%)",
            "avg_roce": "Avg ROCE (%)",
            "avg_npm": "Avg Net Profit Margin (%)",
            "avg_opm": "Avg Operating Margin (%)",
            "avg_de": "Avg D/E",
            "avg_interest_coverage": "Avg Interest Coverage",
            "avg_revenue_cagr": "Revenue CAGR 5Y (%)",
            "avg_pat_cagr": "PAT CAGR 5Y (%)",
            "avg_eps_cagr": "EPS CAGR 5Y (%)",
            "total_fcf": "Total FCF (₹ Cr)",
        }
    )

    numeric = [
        "Market Cap (₹ Cr)",
        "Avg Quality Score",
        "Avg ROE (%)",
        "Avg ROCE (%)",
        "Avg Net Profit Margin (%)",
        "Avg Operating Margin (%)",
        "Avg D/E",
        "Avg Interest Coverage",
        "Revenue CAGR 5Y (%)",
        "PAT CAGR 5Y (%)",
        "EPS CAGR 5Y (%)",
        "Total FCF (₹ Cr)",
    ]

    for column in numeric:

        if column in result.columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            ).round(2)

    return result


def create_quality_chart(summary):
    """
    Sector average composite quality score.
    """

    chart_df = summary.dropna(
        subset=["avg_quality_score"]
    ).sort_values(
        "avg_quality_score",
        ascending=True,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=chart_df["avg_quality_score"],
            y=chart_df["broad_sector"],
            orientation="h",
            name="Average Quality Score",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Average Score: %{x:.2f}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title="Average Composite Quality Score by Sector",
        xaxis_title="Average Composite Quality Score",
        yaxis_title="Sector",
        height=520,
        margin=dict(
            l=40,
            r=30,
            t=70,
            b=40,
        ),
    )

    return figure


def create_profitability_chart(summary):
    """
    Compare average ROE and ROCE by sector.
    """

    chart_df = summary.dropna(
        subset=[
            "avg_roe",
            "avg_roce",
        ],
        how="all",
    ).sort_values(
        "avg_roe",
        ascending=False,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=chart_df["broad_sector"],
            y=chart_df["avg_roe"],
            name="ROE",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "ROE: %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            x=chart_df["broad_sector"],
            y=chart_df["avg_roce"],
            name="ROCE",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "ROCE: %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title="Sector Profitability — Average ROE vs ROCE",
        xaxis_title="Sector",
        yaxis_title="Percentage (%)",
        barmode="group",
        height=520,
        margin=dict(
            l=50,
            r=30,
            t=70,
            b=100,
        ),
    )

    return figure


def create_market_cap_chart(summary):
    """
    Sector market-cap distribution.
    """

    chart_df = summary.dropna(
        subset=["market_cap_crore"]
    ).sort_values(
        "market_cap_crore",
        ascending=True,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=chart_df["market_cap_crore"],
            y=chart_df["broad_sector"],
            orientation="h",
            name="Market Cap",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Market Cap: ₹%{x:,.2f} Cr"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title="Total Market Capitalisation by Sector",
        xaxis_title="Market Capitalisation (₹ Cr)",
        yaxis_title="Sector",
        height=520,
        margin=dict(
            l=40,
            r=30,
            t=70,
            b=40,
        ),
    )

    return figure


# ------------------------------------------------------------------
# Page Header
# ------------------------------------------------------------------

st.title("🏭 Sector Analysis")

st.caption(
    "Analyse sector-level profitability, financial quality, "
    "growth, leverage and market capitalisation across the "
    "official Nifty 100 company universe."
)


# ------------------------------------------------------------------
# Load Data
# ------------------------------------------------------------------

df = get_sector_data()

if df.empty:

    st.warning(
        "Sector analytics data is unavailable."
    )

    st.stop()


df = numeric_columns(df)


# ------------------------------------------------------------------
# Validate Official Universe
# ------------------------------------------------------------------

official_company_count = (
    df["company_id"]
    .dropna()
    .nunique()
)


# ------------------------------------------------------------------
# Latest Financial Year
# ------------------------------------------------------------------

available_years = (
    pd.to_numeric(
        df["year"],
        errors="coerce",
    )
    .dropna()
)

latest_year = (
    int(available_years.max())
    if not available_years.empty
    else None
)


if latest_year is not None:

    st.info(
        f"Sector analytics based on the latest "
        f"available financial year: **{latest_year}**"
    )


# ------------------------------------------------------------------
# Sector Summary
# ------------------------------------------------------------------

sector_summary = build_sector_summary(df)


if sector_summary.empty:

    st.warning(
        "Sector-level aggregation could not be generated."
    )

    st.stop()


# ------------------------------------------------------------------
# Overview KPIs
# ------------------------------------------------------------------

sector_count = (
    sector_summary["broad_sector"]
    .nunique()
)

best_quality_row = sector_summary.loc[
    sector_summary["avg_quality_score"].idxmax()
]

best_roe_row = sector_summary.loc[
    sector_summary["avg_roe"].idxmax()
]

largest_market_cap_row = sector_summary.loc[
    sector_summary["market_cap_crore"].idxmax()
]


st.subheader("📊 Sector Overview")


kpi1, kpi2, kpi3, kpi4 = st.columns(4)


with kpi1:

    st.metric(
        "Broad Sectors",
        sector_count,
    )


with kpi2:

    st.metric(
        "Companies Covered",
        official_company_count,
    )


with kpi3:

    st.metric(
        "Highest Avg Quality",
        best_quality_row["broad_sector"],
        f'{best_quality_row["avg_quality_score"]:.2f}',
    )


with kpi4:

    st.metric(
        "Highest Avg ROE",
        best_roe_row["broad_sector"],
        f'{best_roe_row["avg_roe"]:.2f}%',
    )


st.caption(
    f"Largest sector by market capitalisation: "
    f"**{largest_market_cap_row['broad_sector']}** "
    f"(₹{largest_market_cap_row['market_cap_crore']:,.2f} Cr)"
)


# ------------------------------------------------------------------
# Sector Quality
# ------------------------------------------------------------------

st.subheader("🏆 Sector Quality")

quality_chart = create_quality_chart(
    sector_summary
)

st.plotly_chart(
    quality_chart,
    use_container_width=True,
)


# ------------------------------------------------------------------
# Profitability
# ------------------------------------------------------------------

st.subheader("💰 Sector Profitability")

profitability_chart = create_profitability_chart(
    sector_summary
)

st.plotly_chart(
    profitability_chart,
    use_container_width=True,
)


# ------------------------------------------------------------------
# Market Capitalisation
# ------------------------------------------------------------------

st.subheader("💹 Sector Market Capitalisation")

market_cap_chart = create_market_cap_chart(
    sector_summary
)

st.plotly_chart(
    market_cap_chart,
    use_container_width=True,
)


# ------------------------------------------------------------------
# Sector Ranking Table
# ------------------------------------------------------------------

st.subheader("📋 Sector Ranking")

ranking_df = sector_summary.copy()

ranking_df["Quality Rank"] = (
    ranking_df["avg_quality_score"]
    .rank(
        ascending=False,
        method="min",
    )
)

ranking_df = ranking_df.sort_values(
    "avg_quality_score",
    ascending=False,
)

ranking_df["Quality Rank"] = (
    ranking_df["Quality Rank"]
    .astype("Int64")
)


display_ranking = format_sector_table(
    ranking_df
)

st.dataframe(
    display_ranking,
    use_container_width=True,
    hide_index=True,
)


# ------------------------------------------------------------------
# Sector Detail
# ------------------------------------------------------------------

st.subheader("🔎 Sector Detail")

sector_options = (
    sector_summary["broad_sector"]
    .dropna()
    .sort_values()
    .tolist()
)


selected_sector = st.selectbox(
    "Select Sector",
    sector_options,
)


selected_sector_summary = sector_summary[
    sector_summary["broad_sector"]
    == selected_sector
]


if not selected_sector_summary.empty:

    selected_sector_row = (
        selected_sector_summary.iloc[0]
    )

    detail1, detail2, detail3, detail4 = st.columns(4)

    with detail1:

        value = selected_sector_row[
            "avg_quality_score"
        ]

        st.metric(
            "Avg Quality Score",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}",
        )

    with detail2:

        value = selected_sector_row[
            "avg_roe"
        ]

        st.metric(
            "Avg ROE",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}%",
        )

    with detail3:

        value = selected_sector_row[
            "avg_roce"
        ]

        st.metric(
            "Avg ROCE",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}%",
        )

    with detail4:

        value = selected_sector_row[
            "avg_npm"
        ]

        st.metric(
            "Avg Net Profit Margin",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}%",
        )


    detail5, detail6, detail7, detail8 = st.columns(4)

    with detail5:

        value = selected_sector_row[
            "avg_de"
        ]

        st.metric(
            "Avg D/E",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}",
        )

    with detail6:

        value = selected_sector_row[
            "avg_interest_coverage"
        ]

        st.metric(
            "Avg Interest Coverage",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}",
        )

    with detail7:

        value = selected_sector_row[
            "avg_revenue_cagr"
        ]

        st.metric(
            "Revenue CAGR 5Y",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}%",
        )

    with detail8:

        value = selected_sector_row[
            "avg_pat_cagr"
        ]

        st.metric(
            "PAT CAGR 5Y",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}%",
        )


# ------------------------------------------------------------------
# Companies Within Selected Sector
# ------------------------------------------------------------------

st.subheader(
    f"🏢 Companies in {selected_sector}"
)


sector_companies = df[
    df["broad_sector"]
    == selected_sector
].copy()


sector_companies = sector_companies.sort_values(
    "composite_quality_score",
    ascending=False,
)


company_display = sector_companies[
    [
        "company_id",
        "company_name",
        "sub_sector",
        "composite_quality_score",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "revenue_cagr_5y",
        "pat_cagr_5y",
        "market_cap_crore",
    ]
].copy()


company_display = company_display.rename(
    columns={
        "company_id": "Company ID",
        "company_name": "Company Name",
        "sub_sector": "Sub-Sector",
        "composite_quality_score": "Quality Score",
        "return_on_equity_pct": "ROE (%)",
        "return_on_capital_employed_pct": "ROCE (%)",
        "net_profit_margin_pct": "Net Profit Margin (%)",
        "debt_to_equity": "D/E",
        "interest_coverage": "Interest Coverage",
        "revenue_cagr_5y": "Revenue CAGR 5Y (%)",
        "pat_cagr_5y": "PAT CAGR 5Y (%)",
        "market_cap_crore": "Market Cap (₹ Cr)",
    }
)


numeric_display_columns = [
    "Quality Score",
    "ROE (%)",
    "ROCE (%)",
    "Net Profit Margin (%)",
    "D/E",
    "Interest Coverage",
    "Revenue CAGR 5Y (%)",
    "PAT CAGR 5Y (%)",
    "Market Cap (₹ Cr)",
]


for column in numeric_display_columns:

    if column in company_display.columns:

        company_display[column] = pd.to_numeric(
            company_display[column],
            errors="coerce",
        ).round(2)


st.dataframe(
    company_display,
    use_container_width=True,
    hide_index=True,
)


# ------------------------------------------------------------------
# Data Quality Note
# ------------------------------------------------------------------

st.caption(
    "Sector metrics are aggregated from the validated "
    "company-level financial analytics. N/A values indicate "
    "that the underlying metric is unavailable."
)