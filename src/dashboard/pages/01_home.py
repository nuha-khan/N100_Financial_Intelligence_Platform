import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_sectors,
)


# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
)


# ------------------------------------------------------------------
# Load Data
# ------------------------------------------------------------------

companies = get_companies()
sectors = get_sectors()


# ------------------------------------------------------------------
# Year Selection
# ------------------------------------------------------------------

st.sidebar.header("Dashboard Filters")

# Get available years from financial data
all_ratios = []

for ticker in companies["id"].dropna():
    ratios = get_ratios(ticker)

    if not ratios.empty:
        all_ratios.append(ratios)

if not all_ratios:
    st.error("No financial data available.")
    st.stop()

financial_data = pd.concat(
    all_ratios,
    ignore_index=True,
)

available_years = sorted(
    financial_data["year"]
    .dropna()
    .unique()
)

available_years = [
    int(year)
    for year in available_years
]

selected_year = st.sidebar.selectbox(
    "Financial Year",
    available_years,
    index=len(available_years) - 1,
)


# ------------------------------------------------------------------
# Filter Selected Year
# ------------------------------------------------------------------

latest_data = financial_data[
    financial_data["year"] == selected_year
].copy()


# ------------------------------------------------------------------
# Company Master Mapping
# ------------------------------------------------------------------

company_names = companies[
    ["id", "company_name"]
].rename(
    columns={
        "id": "company_id",
    }
)

latest_data = latest_data.merge(
    company_names,
    on="company_id",
    how="left",
)


# ------------------------------------------------------------------
# Sector Mapping
# ------------------------------------------------------------------

if "company_id" in sectors.columns:

    sector_columns = [
        column
        for column in [
            "company_id",
            "sector",
            "broad_sector",
            "sub_sector",
        ]
        if column in sectors.columns
    ]

    if len(sector_columns) > 1:

        latest_data = latest_data.merge(
            sectors[sector_columns].drop_duplicates(
                subset=["company_id"]
            ),
            on="company_id",
            how="left",
        )


# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------

st.title("📊 Nifty 100 Analytics")

st.caption(
    f"Financial overview of the Nifty 100 universe — {selected_year}"
)


# ------------------------------------------------------------------
# KPI Calculations
# ------------------------------------------------------------------

average_roe = latest_data[
    "return_on_equity_pct"
].mean()

median_de = latest_data[
    "debt_to_equity"
].median()

total_companies = latest_data[
    "company_id"
].nunique()

median_revenue_cagr = latest_data[
    "revenue_cagr_5y"
].median()

debt_free_count = (
    latest_data[
        "debt_to_equity"
    ]
    .fillna(float("inf"))
    .le(0)
    .sum()
)


# ------------------------------------------------------------------
# P/E
# ------------------------------------------------------------------

# P/E is not currently present in financial_ratios.
# Display N/A until the valuation module is completed on Day 26.

median_pe = None


# ------------------------------------------------------------------
# KPI Tiles
# ------------------------------------------------------------------

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        "Average ROE",
        f"{average_roe:.2f}%",
    )

with col2:
    if median_pe is not None:
        st.metric(
            "Median P/E",
            f"{median_pe:.2f}",
        )
    else:
        st.metric(
            "Median P/E",
            "N/A",
        )

with col3:
    st.metric(
        "Median D/E",
        f"{median_de:.2f}",
    )

with col4:
    st.metric(
        "Total Companies",
        f"{total_companies}",
    )

with col5:
    st.metric(
        "Median Revenue CAGR",
        f"{median_revenue_cagr:.2f}%",
    )

with col6:
    st.metric(
        "Debt-Free Companies",
        f"{debt_free_count}",
    )


st.divider()


# ------------------------------------------------------------------
# Sector Breakdown
# ------------------------------------------------------------------

st.subheader("Sector Breakdown")

if "broad_sector" in latest_data.columns:

    sector_counts = (
        latest_data[
            ["company_id", "broad_sector"]
        ]
        .dropna(subset=["broad_sector"])
        .drop_duplicates("company_id")
        .groupby("broad_sector")
        .size()
        .reset_index(name="company_count")
        .sort_values(
            "company_count",
            ascending=False,
        )
    )

    if not sector_counts.empty:

        fig = px.pie(
            sector_counts,
            names="broad_sector",
            values="company_count",
            hole=0.55,
            title="Companies by Sector",
        )

        fig.update_layout(
            height=500,
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    else:
        st.info(
            "Sector information is not available."
        )

else:

    st.info(
        "Sector information is not available in the current database."
    )


# ------------------------------------------------------------------
# Top 5 Companies
# ------------------------------------------------------------------

st.subheader(
    "Top 5 Companies by Composite Quality Score"
)

top5 = (
    latest_data[
        [
            "company_id",
            "company_name",
            "composite_quality_score",
        ]
    ]
    .dropna(
        subset=["composite_quality_score"]
    )
    .sort_values(
        "composite_quality_score",
        ascending=False,
    )
    .head(5)
    .copy()
)

top5 = top5.rename(
    columns={
        "company_id": "Company ID",
        "company_name": "Company",
        "composite_quality_score": "Composite Score",
    }
)

top5["Composite Score"] = (
    top5["Composite Score"]
    .round(2)
)

st.dataframe(
    top5,
    use_container_width=True,
    hide_index=True,
)