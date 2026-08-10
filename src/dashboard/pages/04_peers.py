import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_peers,
    get_ratios,
    _read_query,
)


# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Peer Comparison | Nifty 100 Analytics",
    layout="wide",
)


# ------------------------------------------------------------------
# Peer Metrics
# ------------------------------------------------------------------

PEER_METRICS = {
    "ROE (%)": "return_on_equity_pct",
    "ROCE (%)": "return_on_capital_employed_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
    "Revenue CAGR (5Y)": "revenue_cagr_5y",
    "PAT CAGR (5Y)": "pat_cagr_5y",
}


# ------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------

def get_latest_year():
    """
    Return the latest financial year available in the database.
    """

    result = _read_query(
        """
        SELECT MAX(year) AS latest_year
        FROM financial_ratios
        """
    )

    if result.empty or pd.isna(result.iloc[0]["latest_year"]):
        return None

    return int(result.iloc[0]["latest_year"])


def get_peer_group_names():
    """
    Return all available peer-group names.
    """

    result = _read_query(
        """
        SELECT DISTINCT peer_group_name
        FROM peer_groups
        WHERE peer_group_name IS NOT NULL
        ORDER BY peer_group_name
        """
    )

    if result.empty:
        return []

    return result["peer_group_name"].tolist()


def get_peer_percentile_data(peer_group, year):
    """
    Load the already-calculated Sprint 3 peer percentile data.

    This intentionally uses peer_percentiles instead of recalculating
    percentile ranks inside the dashboard.
    """

    if not peer_group or year is None:
        return pd.DataFrame()

    query = """
        SELECT
            pp.company_id,
            pp.metric,
            pp.percentile_rank
        FROM peer_percentiles pp
        INNER JOIN peer_groups pg
            ON pp.company_id = pg.company_id
        WHERE pg.peer_group_name = ?
          AND pp.year = ?
        ORDER BY pp.company_id, pp.metric
    """

    return _read_query(
        query,
        [peer_group, year],
    )


def get_latest_peer_ratios(peer_company_ids, year):
    """
    Return the raw latest-year financial metrics for the selected
    peer group.

    These are used for the comparison table. Percentiles themselves
    are taken directly from the Sprint 3 peer_percentiles table.
    """

    if not peer_company_ids or year is None:
        return pd.DataFrame()

    placeholders = ",".join(
        ["?"] * len(peer_company_ids)
    )

    query = f"""
        SELECT
            fr.company_id,
            fr.year,
            fr.return_on_equity_pct,
            fr.return_on_capital_employed_pct,
            fr.net_profit_margin_pct,
            fr.debt_to_equity,
            fr.interest_coverage,
            fr.asset_turnover,
            fr.revenue_cagr_5y,
            fr.pat_cagr_5y
        FROM financial_ratios fr
        INNER JOIN (
            SELECT
                company_id,
                MAX(year) AS latest_year
            FROM financial_ratios
            WHERE company_id IN ({placeholders})
              AND year <= ?
            GROUP BY company_id
        ) latest
            ON fr.company_id = latest.company_id
           AND fr.year = latest.latest_year
        WHERE fr.company_id IN ({placeholders})
        ORDER BY fr.company_id
    """

    params = (
        peer_company_ids
        + [year]
        + peer_company_ids
    )

    return _read_query(
        query,
        params,
    )


def build_peer_dataframe(
    peer_group_df,
    companies_df,
    ratio_df,
):
    """
    Combine peer-group membership, company names and raw financial
    metrics into one dataframe.
    """

    if peer_group_df.empty:
        return pd.DataFrame()

    company_names = companies_df[
        ["id", "company_name"]
    ].drop_duplicates(
        subset=["id"]
    )

    result = peer_group_df[
        [
            "company_id",
            "is_benchmark",
        ]
    ].drop_duplicates(
        subset=["company_id"]
    ).copy()

    result = result.merge(
        company_names,
        left_on="company_id",
        right_on="id",
        how="left",
    )

    result.drop(
        columns=["id"],
        inplace=True,
        errors="ignore",
    )

    result["company_name"] = result[
        "company_name"
    ].fillna(
        result["company_id"]
    )

    result = result.merge(
        ratio_df,
        on="company_id",
        how="left",
    )

    return result


def build_percentile_matrix(
    percentile_df,
):
    """
    Convert the existing peer_percentiles table into:

        company_id | metric1 | metric2 | ...

    using the already-calculated percentile_rank values.
    """

    if percentile_df.empty:
        return pd.DataFrame()

    pivot = percentile_df.pivot_table(
        index="company_id",
        columns="metric",
        values="percentile_rank",
        aggfunc="first",
    ).reset_index()

    return pivot


def get_metric_percentile_name(metric_column):
    """
    Convert the financial-ratio column name into the metric name
    used by peer_percentiles.
    """

    mapping = {
        "return_on_equity_pct": "return_on_equity_pct",
        "return_on_capital_employed_pct":
            "return_on_capital_employed_pct",
        "net_profit_margin_pct":
            "net_profit_margin_pct",
        "debt_to_equity": "debt_to_equity",
        "interest_coverage": "interest_coverage",
        "asset_turnover": "asset_turnover",
        "revenue_cagr_5y": "revenue_cagr_5y",
        "pat_cagr_5y": "pat_cagr_5y",
    }

    return mapping.get(metric_column)


def create_radar_chart(
    percentile_matrix,
    peer_df,
    selected_company,
):
    """
    Create the radar chart using the already-calculated Sprint 3
    percentile ranks.

    Selected company percentile is compared against the average
    percentile of its peer group.
    """

    if percentile_matrix.empty:
        return None

    selected_rows = percentile_matrix[
        percentile_matrix["company_id"]
        == selected_company
    ]

    if selected_rows.empty:
        return None

    selected_row = selected_rows.iloc[0]

    categories = []
    selected_values = []
    peer_average_values = []

    for display_name, metric_column in PEER_METRICS.items():

        metric_name = get_metric_percentile_name(
            metric_column
        )

        if metric_name not in percentile_matrix.columns:
            continue

        selected_value = pd.to_numeric(
            selected_row.get(metric_name),
            errors="coerce",
        )

        peer_values = pd.to_numeric(
            percentile_matrix[metric_name],
            errors="coerce",
        )

        peer_average = peer_values.mean()

        if pd.isna(selected_value):
            continue

        categories.append(display_name)

        selected_values.append(
            float(selected_value)
        )

        peer_average_values.append(
            0.0
            if pd.isna(peer_average)
            else float(peer_average)
        )

    if not categories:
        return None

    # Close radar polygons
    categories_closed = categories + [
        categories[0]
    ]

    selected_closed = selected_values + [
        selected_values[0]
    ]

    average_closed = peer_average_values + [
        peer_average_values[0]
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Scatterpolar(
            r=selected_closed,
            theta=categories_closed,
            fill="toself",
            name=selected_company,
            line=dict(
                width=2,
            ),
        )
    )

    figure.add_trace(
        go.Scatterpolar(
            r=average_closed,
            theta=categories_closed,
            fill="toself",
            name="Peer Average",
            line=dict(
                width=2,
            ),
        )
    )

    figure.update_layout(
        title="Company vs Peer Group Average — Percentile Rank",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickformat=".0%",
            )
        ),
        showlegend=True,
        height=550,
        margin=dict(
            l=40,
            r=40,
            t=80,
            b=40,
        ),
    )

    return figure


# ------------------------------------------------------------------
# Page Header
# ------------------------------------------------------------------

st.title("🤝 Peer Comparison")

st.caption(
    "Compare companies within their peer group using the "
    "validated peer analytics calculated during Sprint 3."
)


# ------------------------------------------------------------------
# Load Company Data
# ------------------------------------------------------------------

companies = get_companies()

if companies.empty:

    st.warning(
        "Company data is unavailable."
    )

    st.stop()


# ------------------------------------------------------------------
# Latest Financial Year
# ------------------------------------------------------------------

latest_year = get_latest_year()

if latest_year is None:

    st.warning(
        "No financial year is available."
    )

    st.stop()


st.caption(
    f"Peer analytics based on the latest available "
    f"financial year: {latest_year}"
)


# ------------------------------------------------------------------
# Peer Group Names
# ------------------------------------------------------------------

peer_group_names = get_peer_group_names()

if not peer_group_names:

    st.warning(
        "No peer groups are available."
    )

    st.stop()


# ------------------------------------------------------------------
# Peer Group Selector
# ------------------------------------------------------------------

selected_peer_group = st.selectbox(
    "Peer Group",
    peer_group_names,
)


peer_group_df = get_peers(
    selected_peer_group
)


if peer_group_df.empty:

    st.info(
        "No companies are available in this peer group."
    )

    st.stop()


# ------------------------------------------------------------------
# Peer Company IDs
# ------------------------------------------------------------------

peer_company_ids = (
    peer_group_df["company_id"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .tolist()
)


# ------------------------------------------------------------------
# Load Existing Sprint 3 Analytics
# ------------------------------------------------------------------

percentile_df = get_peer_percentile_data(
    selected_peer_group,
    latest_year,
)


# ------------------------------------------------------------------
# Load Raw Latest-Year Metrics
# ------------------------------------------------------------------

ratio_df = get_latest_peer_ratios(
    peer_company_ids,
    latest_year,
)


# ------------------------------------------------------------------
# Build Peer Dataframe
# ------------------------------------------------------------------

peer_df = build_peer_dataframe(
    peer_group_df,
    companies,
    ratio_df,
)


if peer_df.empty:

    st.warning(
        "Financial data is unavailable for the selected peer group."
    )

    st.stop()


# ------------------------------------------------------------------
# Build Percentile Matrix
# ------------------------------------------------------------------

percentile_matrix = build_percentile_matrix(
    percentile_df
)


# ------------------------------------------------------------------
# Company Selector
# ------------------------------------------------------------------

company_options = peer_df[
    [
        "company_id",
        "company_name",
    ]
].drop_duplicates(
    subset=["company_id"]
)


company_labels = {
    row["company_id"]: (
        f"{row['company_name']} "
        f"({row['company_id']})"
    )
    for _, row in company_options.iterrows()
}


selected_company = st.selectbox(
    "Select Company",
    company_options[
        "company_id"
    ].tolist(),
    format_func=lambda ticker: company_labels.get(
        ticker,
        ticker,
    ),
)


# ------------------------------------------------------------------
# Selected Company Information
# ------------------------------------------------------------------

selected_rows = peer_df[
    peer_df["company_id"]
    == selected_company
]

if selected_rows.empty:

    st.warning(
        "Selected company data is unavailable."
    )

    st.stop()


selected_row = selected_rows.iloc[0]


benchmark_value = selected_row.get(
    "is_benchmark",
    0,
)


benchmark_status = (
    "Benchmark Company"
    if benchmark_value == 1
    else "Peer Company"
)


st.markdown(
    f"### {selected_row['company_name']} "
    f"({selected_company})"
)

st.caption(
    benchmark_status
)


# ------------------------------------------------------------------
# Radar Chart
# ------------------------------------------------------------------

st.subheader(
    "📊 Peer Benchmark Radar"
)

if percentile_matrix.empty:

    st.info(
        "Peer percentile analytics are not available "
        "for this peer group."
    )

else:

    radar = create_radar_chart(
        percentile_matrix,
        peer_df,
        selected_company,
    )

    if radar is not None:

        st.plotly_chart(
            radar,
            use_container_width=True,
        )

    else:

        st.info(
            "Not enough percentile data is available "
            "to generate the radar chart."
        )


# ------------------------------------------------------------------
# KPI Comparison
# ------------------------------------------------------------------

st.subheader(
    "📋 Peer Group Comparison"
)


comparison_columns = [
    "company_id",
    "company_name",
    "is_benchmark",
]

comparison_columns.extend(
    PEER_METRICS.values()
)


available_columns = [
    column
    for column in comparison_columns
    if column in peer_df.columns
]


comparison_df = peer_df[
    available_columns
].copy()


# ------------------------------------------------------------------
# Rename Columns
# ------------------------------------------------------------------

comparison_df = comparison_df.rename(
    columns={
        "company_id": "Company ID",
        "company_name": "Company Name",
        "is_benchmark": "Benchmark",
        **{
            column: display_name
            for display_name, column
            in PEER_METRICS.items()
        },
    }
)


# ------------------------------------------------------------------
# Benchmark Yes / No
# ------------------------------------------------------------------

if "Benchmark" in comparison_df.columns:

    comparison_df["Benchmark"] = (
        comparison_df["Benchmark"]
        .apply(
            lambda value:
                "Yes"
                if value == 1
                else "No"
        )
    )


# ------------------------------------------------------------------
# Format Numeric Metrics
# ------------------------------------------------------------------

for column in PEER_METRICS.keys():

    if column in comparison_df.columns:

        comparison_df[column] = pd.to_numeric(
            comparison_df[column],
            errors="coerce",
        ).round(2)


# ------------------------------------------------------------------
# Benchmark First
# ------------------------------------------------------------------

if "Benchmark" in comparison_df.columns:

    comparison_df["_benchmark_sort"] = (
        comparison_df["Benchmark"]
        .eq("Yes")
        .astype(int)
    )

    comparison_df = (
        comparison_df
        .sort_values(
            "_benchmark_sort",
            ascending=False,
        )
        .drop(
            columns="_benchmark_sort"
        )
    )


# ------------------------------------------------------------------
# Highlight Benchmark Row
# ------------------------------------------------------------------

def highlight_benchmark(row):

    if row.get("Benchmark") == "Yes":

        return [
            "background-color: #FFF2CC"
            for _ in row
        ]

    return [
        ""
        for _ in row
    ]


styled_comparison = comparison_df.style.apply(
    highlight_benchmark,
    axis=1,
)


st.dataframe(
    styled_comparison,
    use_container_width=True,
    hide_index=True,
)


# ------------------------------------------------------------------
# Missing Data Note
# ------------------------------------------------------------------

if comparison_df.isna().any().any():

    st.caption(
        "Note: N/A values indicate that the corresponding "
        "financial metric is unavailable for that company."
    )


# ------------------------------------------------------------------
# Analytics Source Note
# ------------------------------------------------------------------

st.caption(
    "Radar percentile values are sourced from the peer "
    "percentile calculations completed during Sprint 3. "
    "The comparison table displays the corresponding "
    "latest-year financial metrics."
)