import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_pl,
    get_bs,
    get_cf,
    get_ratios,
)


# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Trend Analysis | Nifty 100 Analytics",
    layout="wide",
)


# ------------------------------------------------------------------
# Metric Configuration
# ------------------------------------------------------------------

METRICS = {
    "Revenue": {
        "source": "pl",
        "column": "sales",
        "label": "Revenue (₹ Cr)",
    },
    "Net Profit": {
        "source": "pl",
        "column": "net_profit",
        "label": "Net Profit (₹ Cr)",
    },
    "EPS": {
        "source": "pl",
        "column": "eps",
        "label": "EPS (₹)",
    },
    "Operating Profit": {
        "source": "pl",
        "column": "operating_profit",
        "label": "Operating Profit (₹ Cr)",
    },
    "Total Assets": {
        "source": "bs",
        "column": "total_assets",
        "label": "Total Assets (₹ Cr)",
    },
    "Borrowings": {
        "source": "bs",
        "column": "borrowings",
        "label": "Borrowings (₹ Cr)",
    },
    "Cash From Operations": {
        "source": "cf",
        "column": "operating_activity",
        "label": "Cash From Operations (₹ Cr)",
    },
}


# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------

def get_metric_history(ticker, metric_name):
    """
    Return historical data for the selected metric.
    """

    config = METRICS[metric_name]

    source = config["source"]
    column = config["column"]

    if source == "pl":
        df = get_pl(ticker)

    elif source == "bs":
        df = get_bs(ticker)

    elif source == "cf":
        df = get_cf(ticker)

    else:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    if "year" not in df.columns or column not in df.columns:
        return pd.DataFrame()

    result = df[
        ["year", column]
    ].copy()

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce",
    )

    result[column] = pd.to_numeric(
        result[column],
        errors="coerce",
    )

    result = result.dropna(
        subset=["year"]
    )

    result = result.sort_values(
        "year"
    )

    # Keep the latest 10 available years
    result = result.tail(10)

    return result


def calculate_yoy(df, value_column):
    """
    Calculate year-over-year percentage change.

    For negative/zero base values, percentage change may not
    be meaningful, so those cases are returned as NaN.
    """

    result = df.copy()

    previous = result[value_column].shift(1)

    result["yoy_pct"] = (
        (result[value_column] - previous)
        / previous.abs()
    ) * 100

    invalid_base = (
        previous.isna()
        | (previous == 0)
    )

    result.loc[
        invalid_base,
        "yoy_pct"
    ] = pd.NA

    return result


def get_cagr_summary(ticker):
    """
    Retrieve already-computed CAGR values from financial_ratios.

    No CAGR is recalculated here.
    """

    ratios = get_ratios(ticker)

    if ratios.empty:
        return None

    ratios = ratios.copy()

    if "year" in ratios.columns:
        ratios["year"] = pd.to_numeric(
            ratios["year"],
            errors="coerce",
        )

        ratios = ratios.sort_values(
            "year"
        )

    latest = ratios.iloc[-1]

    return {
        "Revenue CAGR 5Y": latest.get(
            "revenue_cagr_5y"
        ),
        "PAT CAGR 5Y": latest.get(
            "pat_cagr_5y"
        ),
        "EPS CAGR 5Y": latest.get(
            "eps_cagr_5y"
        ),
    }


def normalize_metric(df, value_column):
    """
    Normalize a metric to 100 at its first valid observation.

    Useful for comparing metrics with different scales.
    """

    result = df.copy()

    valid_values = result[value_column].dropna()

    if valid_values.empty:
        result["normalized"] = pd.NA
        return result

    base_value = valid_values.iloc[0]

    if pd.isna(base_value) or base_value == 0:
        result["normalized"] = pd.NA
        return result

    result["normalized"] = (
        result[value_column]
        / base_value
    ) * 100

    return result


def create_trend_chart(
    df,
    value_column,
    display_label,
    metric_name,
):
    """
    Create historical trend chart.
    """

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=df["year"],
            y=df[value_column],
            mode="lines+markers",
            name=metric_name,
            hovertemplate=(
                "<b>Year:</b> %{x}<br>"
                f"<b>{display_label}:</b> %{{y:.2f}}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title=f"{metric_name} — 10-Year Trend",
        xaxis_title="Financial Year",
        yaxis_title=display_label,
        hovermode="x unified",
        height=500,
        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50,
        ),
    )

    return figure


def create_overlay_chart(
    ticker,
    selected_metrics,
):
    """
    Create normalized multi-metric trend chart.

    Each metric starts at 100 in its first available year.
    """

    figure = go.Figure()

    added = False

    for metric_name in selected_metrics:

        history = get_metric_history(
            ticker,
            metric_name,
        )

        if history.empty:
            continue

        column = METRICS[
            metric_name
        ]["column"]

        normalized = normalize_metric(
            history,
            column,
        )

        if normalized["normalized"].isna().all():
            continue

        figure.add_trace(
            go.Scatter(
                x=normalized["year"],
                y=normalized["normalized"],
                mode="lines+markers",
                name=metric_name,
            )
        )

        added = True

    if not added:
        return None

    figure.update_layout(
        title="Normalized Multi-Metric Trend",
        xaxis_title="Financial Year",
        yaxis_title="Indexed Value (First Year = 100)",
        hovermode="x unified",
        height=500,
        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50,
        ),
    )

    return figure


# ------------------------------------------------------------------
# Page Header
# ------------------------------------------------------------------

st.title("📈 Trend Analysis")

st.caption(
    "Analyse historical financial performance, year-over-year "
    "changes and long-term growth trends for Nifty 100 companies."
)


# ------------------------------------------------------------------
# Load Companies
# ------------------------------------------------------------------

companies = get_companies()

if companies.empty:

    st.warning(
        "Company data is unavailable."
    )

    st.stop()


companies = companies.copy()

company_options = companies[
    ["id", "company_name"]
].drop_duplicates()

company_options = company_options.sort_values(
    "company_name"
)


company_labels = {
    row["id"]: (
        f'{row["company_name"]} ({row["id"]})'
    )
    for _, row in company_options.iterrows()
}


# ------------------------------------------------------------------
# Company Selector
# ------------------------------------------------------------------

selected_ticker = st.selectbox(
    "Select Company",
    company_options["id"].tolist(),
    format_func=lambda ticker: company_labels.get(
        ticker,
        ticker,
    ),
)


# ------------------------------------------------------------------
# Company Information
# ------------------------------------------------------------------

selected_company = companies[
    companies["id"] == selected_ticker
]

if not selected_company.empty:

    company_name = selected_company.iloc[0].get(
        "company_name",
        selected_ticker,
    )

    st.subheader(
        f"{company_name} ({selected_ticker})"
    )


# ------------------------------------------------------------------
# Single Metric Trend
# ------------------------------------------------------------------

st.subheader("Historical Trend")

selected_metric = st.selectbox(
    "Select Metric",
    list(METRICS.keys()),
)


history = get_metric_history(
    selected_ticker,
    selected_metric,
)


if history.empty:

    st.info(
        "Historical data is not available for "
        f"{selected_metric}."
    )

else:

    value_column = METRICS[
        selected_metric
    ]["column"]

    display_label = METRICS[
        selected_metric
    ]["label"]

    history_yoy = calculate_yoy(
        history,
        value_column,
    )

    figure = create_trend_chart(
        history_yoy,
        value_column,
        display_label,
        selected_metric,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )

    if len(history) < 10:

        st.caption(
            f"Showing {len(history)} available years "
            "because complete 10-year historical data is "
            "not available for this company."
        )


# ------------------------------------------------------------------
# YoY Table
# ------------------------------------------------------------------

if not history.empty:

    st.subheader("Year-over-Year Growth")

    yoy_table = history_yoy[
        [
            "year",
            value_column,
            "yoy_pct",
        ]
    ].copy()

    yoy_table = yoy_table.rename(
        columns={
            "year": "Year",
            value_column: METRICS[
                selected_metric
            ]["label"],
            "yoy_pct": "YoY Change (%)",
        }
    )

    yoy_table["Year"] = (
        yoy_table["Year"]
        .astype(int)
    )

    yoy_table[
        "YoY Change (%)"
    ] = pd.to_numeric(
        yoy_table["YoY Change (%)"],
        errors="coerce",
    ).round(2)

    yoy_table[
        METRICS[selected_metric]["label"]
    ] = pd.to_numeric(
        yoy_table[
            METRICS[selected_metric]["label"]
        ],
        errors="coerce",
    ).round(2)

    st.dataframe(
        yoy_table,
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------------
# CAGR Summary
# ------------------------------------------------------------------

st.subheader("Long-Term Growth")

cagr = get_cagr_summary(
    selected_ticker
)


if cagr is None:

    st.info(
        "CAGR data is not available for this company."
    )

else:

    cagr_columns = st.columns(3)

    for column, (label, value) in zip(
        cagr_columns,
        cagr.items(),
    ):

        numeric_value = pd.to_numeric(
            value,
            errors="coerce",
        )

        with column:

            if pd.isna(numeric_value):

                st.metric(
                    label,
                    "N/A",
                )

            else:

                st.metric(
                    label,
                    f"{numeric_value:.2f}%",
                )


# ------------------------------------------------------------------
# Multi-Metric Overlay
# ------------------------------------------------------------------

st.subheader(
    "Multi-Metric Growth Comparison"
)

st.caption(
    "Metrics are indexed to 100 at their first available "
    "year so their relative growth can be compared despite "
    "different units and scales."
)


overlay_metrics = st.multiselect(
    "Select up to 3 metrics",
    list(METRICS.keys()),
    default=[
        "Revenue",
        "Net Profit",
    ],
    max_selections=3,
)


if overlay_metrics:

    overlay = create_overlay_chart(
        selected_ticker,
        overlay_metrics,
    )

    if overlay is not None:

        st.plotly_chart(
            overlay,
            use_container_width=True,
        )

    else:

        st.info(
            "Insufficient historical data to build "
            "the selected comparison."
        )

else:

    st.info(
        "Select at least one metric to display "
        "the multi-metric comparison."
    )


# ------------------------------------------------------------------
# Data Availability Note
# ------------------------------------------------------------------

st.caption(
    "N/A values indicate that the corresponding metric "
    "is unavailable in the underlying financial data."
)