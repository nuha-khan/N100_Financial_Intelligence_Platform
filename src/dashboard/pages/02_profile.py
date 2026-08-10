import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_sectors,
    get_pros_cons,
)


# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Company Profile | Nifty 100 Analytics",
    page_icon="🏢",
    layout="wide",
)


# ------------------------------------------------------------------
# Load Company Master Data
# ------------------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()


companies = companies.copy()

companies["id"] = (
    companies["id"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ------------------------------------------------------------------
# Company Search
# ------------------------------------------------------------------

st.title("🏢 Company Profile")

st.caption(
    "Explore financial performance, company information, "
    "and historical trends."
)

search_text = st.text_input(
    "Search company",
    placeholder="Enter company name or ticker...",
)


# ------------------------------------------------------------------
# Search / Autocomplete
# ------------------------------------------------------------------

if search_text:

    search_value = search_text.strip().lower()

    matches = companies[
        companies["id"]
        .str.lower()
        .str.contains(
            search_value,
            na=False,
        )
        |
        companies["company_name"]
        .fillna("")
        .str.lower()
        .str.contains(
            search_value,
            na=False,
        )
    ].copy()

else:

    matches = companies.copy()


if matches.empty:

    st.warning(
        "Ticker not found — please try another."
    )

    st.stop()


# ------------------------------------------------------------------
# Company Selector
# ------------------------------------------------------------------

matches["display_name"] = (
    matches["id"]
    + " — "
    + matches["company_name"].fillna("")
)

selected_display = st.selectbox(
    "Select Company",
    matches["display_name"].tolist(),
)


selected_ticker = selected_display.split(
    " — ",
    1,
)[0]


company = companies[
    companies["id"] == selected_ticker
].iloc[0]


# ------------------------------------------------------------------
# Load Company Data
# ------------------------------------------------------------------

ratios = get_ratios(
    selected_ticker,
)

pl = get_pl(
    selected_ticker,
)

sectors = get_sectors()

pros_cons = get_pros_cons(
    selected_ticker,
)


# ------------------------------------------------------------------
# Sector Information
# ------------------------------------------------------------------

sector_name = "N/A"
sub_sector_name = "N/A"

if not sectors.empty:

    company_sector = sectors[
        sectors["company_id"].astype(str).str.upper()
        == selected_ticker
    ]

    if not company_sector.empty:

        sector_row = company_sector.iloc[0]

        sector_name = (
            sector_row.get(
                "broad_sector",
                "N/A",
            )
        )

        sub_sector_name = (
            sector_row.get(
                "sub_sector",
                "N/A",
            )
        )


# ------------------------------------------------------------------
# Company Information Card
# ------------------------------------------------------------------

st.subheader(
    company.get(
        "company_name",
        selected_ticker,
    )
)

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:

    st.markdown("**NSE Ticker**")
    st.write(selected_ticker)

with info_col2:

    st.markdown("**Sector**")
    st.write(sector_name)

with info_col3:

    st.markdown("**Sub-sector**")
    st.write(sub_sector_name)


about_company = company.get(
    "about_company",
    None,
)

if pd.notna(about_company) and str(
    about_company
).strip():

    st.markdown("**About the Company**")

    st.write(
        str(about_company)
    )


# ------------------------------------------------------------------
# Latest Financial Year
# ------------------------------------------------------------------

if ratios.empty:

    st.warning(
        "Financial data is not available for this company."
    )

    st.stop()


ratios = ratios.copy()

ratios["year"] = pd.to_numeric(
    ratios["year"],
    errors="coerce",
)

ratios = ratios.dropna(
    subset=["year"]
)

ratios = ratios.sort_values(
    "year"
)

latest_ratio = ratios.iloc[-1]

latest_year = int(
    latest_ratio["year"]
)


# ------------------------------------------------------------------
# KPI Helper
# ------------------------------------------------------------------

def format_percentage(value):

    if pd.isna(value):
        return "N/A"

    return f"{value:.2f}%"


def format_number(value):

    if pd.isna(value):
        return "N/A"

    return f"{value:.2f}"


# ------------------------------------------------------------------
# KPI Values
# ------------------------------------------------------------------

roe = latest_ratio.get(
    "return_on_equity_pct"
)

roce = latest_ratio.get(
    "return_on_capital_employed_pct"
)

npm = latest_ratio.get(
    "net_profit_margin_pct"
)

de = latest_ratio.get(
    "debt_to_equity"
)

revenue_cagr = latest_ratio.get(
    "revenue_cagr_5y"
)

fcf = latest_ratio.get(
    "free_cash_flow_cr"
)


# ------------------------------------------------------------------
# KPI Tiles
# ------------------------------------------------------------------

st.subheader(
    f"Financial Snapshot — {latest_year}"
)

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.metric(
        "ROE",
        format_percentage(roe),
    )

with k2:
    st.metric(
        "ROCE",
        format_percentage(roce),
    )

with k3:
    st.metric(
        "Net Profit Margin",
        format_percentage(npm),
    )

with k4:
    st.metric(
        "Debt / Equity",
        format_number(de),
    )

with k5:
    st.metric(
        "Revenue CAGR (5Y)",
        format_percentage(revenue_cagr),
    )

with k6:
    st.metric(
        "Free Cash Flow",
        (
            "N/A"
            if pd.isna(fcf)
            else f"₹{fcf:,.2f} Cr"
        ),
    )


st.divider()


# ------------------------------------------------------------------
# Prepare P&L Data
# ------------------------------------------------------------------

if pl.empty:

    st.info(
        "Profit & Loss history is not available "
        "for this company."
    )

else:

    pl = pl.copy()

    pl["year"] = pd.to_numeric(
        pl["year"],
        errors="coerce",
    )

    pl["sales"] = pd.to_numeric(
        pl["sales"],
        errors="coerce",
    )

    pl["net_profit"] = pd.to_numeric(
        pl["net_profit"],
        errors="coerce",
    )

    pl = (
        pl.dropna(
            subset=["year"]
        )
        .sort_values("year")
    )


# ------------------------------------------------------------------
# Revenue & Net Profit Chart
# ------------------------------------------------------------------

st.subheader(
    "Revenue & Net Profit — 10-Year Trend"
)

if pl.empty:

    st.info(
        "No historical Profit & Loss data available."
    )

else:

    chart_data = pl.tail(10).copy()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=chart_data["year"],
            y=chart_data["sales"],
            name="Revenue",
            hovertemplate=(
                "Year: %{x}<br>"
                "Revenue: %{y:,.2f} Cr"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Bar(
            x=chart_data["year"],
            y=chart_data["net_profit"],
            name="Net Profit",
            hovertemplate=(
                "Year: %{x}<br>"
                "Net Profit: %{y:,.2f} Cr"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        barmode="group",
        height=450,
        xaxis_title="Year",
        yaxis_title="Amount (₹ Cr)",
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    if len(pl) < 10:

        st.info(
            f"Only {len(pl)} years of financial data "
            "are available for this company."
        )


# ------------------------------------------------------------------
# ROE & ROCE Chart
# ------------------------------------------------------------------

st.subheader(
    "ROE & ROCE — 10-Year Trend"
)

roe_roce = ratios[
    [
        "year",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
    ]
].copy()

roe_roce = roe_roce.tail(10)


fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=roe_roce["year"],
        y=roe_roce[
            "return_on_equity_pct"
        ],
        mode="lines+markers",
        name="ROE",
        hovertemplate=(
            "Year: %{x}<br>"
            "ROE: %{y:.2f}%"
            "<extra></extra>"
        ),
    )
)

fig.add_trace(
    go.Scatter(
        x=roe_roce["year"],
        y=roe_roce[
            "return_on_capital_employed_pct"
        ],
        mode="lines+markers",
        name="ROCE",
        yaxis="y2",
        hovertemplate=(
            "Year: %{x}<br>"
            "ROCE: %{y:.2f}%"
            "<extra></extra>"
        ),
    )
)

fig.update_layout(
    height=450,
    xaxis=dict(
        title="Year",
    ),
    yaxis=dict(
        title="ROE (%)",
    ),
    yaxis2=dict(
        title="ROCE (%)",
        overlaying="y",
        side="right",
    ),
    hovermode="x unified",
    margin=dict(
        l=20,
        r=20,
        t=30,
        b=20,
    ),
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

if len(ratios) < 10:

    st.info(
        f"Only {len(ratios)} years of ratio data "
        "are available for this company."
    )


# ------------------------------------------------------------------
# Pros & Cons
# ------------------------------------------------------------------

st.subheader("Investment Pros & Cons")

if pros_cons.empty:

    st.info(
        "Pros and cons information is not available "
        "for this company."
    )

else:

    col_pros, col_cons = st.columns(2)

    with col_pros:

        st.markdown("### 🟢 Pros")

        pros_items = []

        for value in pros_cons["pros"]:

            if pd.notna(value):

                value = str(value).strip()

                if value and value not in pros_items:
                    pros_items.append(value)

        if pros_items:

            for item in pros_items:
                st.markdown(f"✅ {item}")

        else:

            st.write("No pros available.")

    with col_cons:

        st.markdown("### 🔴 Cons")

        cons_items = []

        for value in pros_cons["cons"]:

            if pd.notna(value):

                value = str(value).strip()

                if value and value not in cons_items:
                    cons_items.append(value)

        if cons_items:

            for item in cons_items:
                st.markdown(f"❌ {item}")

        else:

            st.write("No cons available.")