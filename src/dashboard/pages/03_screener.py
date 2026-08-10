import pandas as pd
import streamlit as st

from src.dashboard.utils.db import get_screener_data


# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Screener | Nifty 100 Analytics",
    layout="wide",
)


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

METRIC_COLUMNS = {
    "ROE (%)": "return_on_equity_pct",
    "D/E": "debt_to_equity",
    "Free Cash Flow": "free_cash_flow_cr",
    "Revenue CAGR (5Y)": "revenue_cagr_5y",
    "PAT CAGR (5Y)": "pat_cagr_5y",
    "OPM (%)": "operating_profit_margin_pct",
    "P/E": "pe_ratio",
    "P/B": "pb_ratio",
    "Dividend Yield (%)": "dividend_yield_pct",
    "Interest Coverage": "interest_coverage",
}


DISPLAY_COLUMNS = [
    "company_id",
    "company_name",
    "broad_sector",
    "composite_quality_score",
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5y",
    "pat_cagr_5y",
    "operating_profit_margin_pct",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "interest_coverage",
]


# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------

def apply_screener_filters(
    df,
    min_roe,
    max_de,
    min_fcf,
    min_revenue_cagr,
    min_pat_cagr,
    min_opm,
    max_pe,
    max_pb,
    min_dividend_yield,
    min_icr,
):
    """
    Apply all screener thresholds to the dataset.

    Missing values are retained for metrics where data is unavailable,
    preventing incomplete company records from being excluded solely
    because a particular metric is unavailable.
    """

    result = df.copy()

    # --------------------------------------------------------------
    # ROE
    # --------------------------------------------------------------

    if min_roe is not None:
        result = result[
            result["return_on_equity_pct"].isna()
            | (result["return_on_equity_pct"] >= min_roe)
        ]

    # --------------------------------------------------------------
    # Debt / Equity
    # --------------------------------------------------------------

    if max_de is not None:
        result = result[
            result["debt_to_equity"].isna()
            | (result["debt_to_equity"] <= max_de)
        ]

    # --------------------------------------------------------------
    # Free Cash Flow
    # --------------------------------------------------------------

    if min_fcf is not None:
        result = result[
            result["free_cash_flow_cr"].isna()
            | (result["free_cash_flow_cr"] >= min_fcf)
        ]

    # --------------------------------------------------------------
    # Revenue CAGR
    # --------------------------------------------------------------

    if min_revenue_cagr is not None:
        result = result[
            result["revenue_cagr_5y"].isna()
            | (result["revenue_cagr_5y"] >= min_revenue_cagr)
        ]

    # --------------------------------------------------------------
    # PAT CAGR
    # --------------------------------------------------------------

    if min_pat_cagr is not None:
        result = result[
            result["pat_cagr_5y"].isna()
            | (result["pat_cagr_5y"] >= min_pat_cagr)
        ]

    # --------------------------------------------------------------
    # Operating Profit Margin
    # --------------------------------------------------------------

    if min_opm is not None:
        result = result[
            result["operating_profit_margin_pct"].isna()
            | (result["operating_profit_margin_pct"] >= min_opm)
        ]

    # --------------------------------------------------------------
    # P/E
    # --------------------------------------------------------------

    if max_pe is not None:
        result = result[
            result["pe_ratio"].isna()
            | (result["pe_ratio"] <= max_pe)
        ]

    # --------------------------------------------------------------
    # P/B
    # --------------------------------------------------------------

    if max_pb is not None:
        result = result[
            result["pb_ratio"].isna()
            | (result["pb_ratio"] <= max_pb)
        ]

    # --------------------------------------------------------------
    # Dividend Yield
    # --------------------------------------------------------------

    if min_dividend_yield is not None:
        result = result[
            result["dividend_yield_pct"].isna()
            | (result["dividend_yield_pct"] >= min_dividend_yield)
        ]

    # --------------------------------------------------------------
    # Interest Coverage
    # --------------------------------------------------------------

    if min_icr is not None:
        result = result[
            result["interest_coverage"].isna()
            | (result["interest_coverage"] >= min_icr)
        ]

    return result


# ------------------------------------------------------------------
# Preset Definitions
# ------------------------------------------------------------------

def get_preset_values(preset):
    """
    Return threshold values for a predefined screener.
    """

    presets = {
        "Quality": {
            "min_roe": 15.0,
            "max_de": 1.0,
            "min_fcf": 0.0,
            "min_revenue_cagr": 0.0,
            "min_pat_cagr": 0.0,
            "min_opm": 0.0,
            "max_pe": 100.0,
            "max_pb": 20.0,
            "min_dividend_yield": 0.0,
            "min_icr": 0.0,
        },

        "Value": {
            "min_roe": 0.0,
            "max_de": 10.0,
            "min_fcf": -999999.0,
            "min_revenue_cagr": -999.0,
            "min_pat_cagr": -999.0,
            "min_opm": -999.0,
            "max_pe": 20.0,
            "max_pb": 3.0,
            "min_dividend_yield": 0.0,
            "min_icr": 0.0,
        },

        "Growth": {
            "min_roe": 0.0,
            "max_de": 10.0,
            "min_fcf": -999999.0,
            "min_revenue_cagr": 0.0,
            "min_pat_cagr": 20.0,
            "min_opm": 0.0,
            "max_pe": 100.0,
            "max_pb": 20.0,
            "min_dividend_yield": 0.0,
            "min_icr": 0.0,
        },

        "Dividend": {
            "min_roe": 0.0,
            "max_de": 10.0,
            "min_fcf": 0.0,
            "min_revenue_cagr": -999.0,
            "min_pat_cagr": -999.0,
            "min_opm": -999.0,
            "max_pe": 100.0,
            "max_pb": 20.0,
            "min_dividend_yield": 2.0,
            "min_icr": 0.0,
        },

        "Debt-Free": {
            "min_roe": 0.0,
            "max_de": 0.0,
            "min_fcf": -999999.0,
            "min_revenue_cagr": -999.0,
            "min_pat_cagr": -999.0,
            "min_opm": -999.0,
            "max_pe": 100.0,
            "max_pb": 20.0,
            "min_dividend_yield": 0.0,
            "min_icr": 0.0,
        },

        "Turnaround": {
            "min_roe": 0.0,
            "max_de": 10.0,
            "min_fcf": 0.0,
            "min_revenue_cagr": 0.0,
            "min_pat_cagr": 0.0,
            "min_opm": 0.0,
            "max_pe": 100.0,
            "max_pb": 20.0,
            "min_dividend_yield": 0.0,
            "min_icr": 1.0,
        },
    }

    return presets[preset]


# ------------------------------------------------------------------
# Load Data
# ------------------------------------------------------------------

st.title("🔎 Nifty 100 Screener")

st.caption(
    "Filter the Nifty 100 universe using financial quality, growth, "
    "valuation, cash-flow and leverage metrics."
)

df = get_screener_data()

if df.empty:
    st.warning(
        "No screener data is available."
    )
    st.stop()


# ------------------------------------------------------------------
# Financial Year
# ------------------------------------------------------------------

available_years = sorted(
    df["year"].dropna().unique(),
    reverse=True,
)

selected_year = st.sidebar.selectbox(
    "Financial Year",
    available_years,
    index=0,
)

df = get_screener_data(
    int(selected_year)
)

if df.empty:
    st.warning(
        f"No screener data is available for {int(selected_year)}."
    )
    st.stop()


# ------------------------------------------------------------------
# Presets
# ------------------------------------------------------------------

st.sidebar.subheader("Preset Screeners")

preset = st.sidebar.radio(
    "Choose a preset",
    [
        "Custom",
        "Quality",
        "Value",
        "Growth",
        "Dividend",
        "Debt-Free",
        "Turnaround",
    ],
)


# ------------------------------------------------------------------
# Default Values
# ------------------------------------------------------------------

# Custom mode intentionally uses very broad limits.
# This allows the complete 92-company database universe to appear
# before the user applies any restrictive filters.

defaults = {
    "min_roe": -100.0,
    "max_de": 100.0,
    "min_fcf": -999999999.0,
    "min_revenue_cagr": -100.0,
    "min_pat_cagr": -100.0,
    "min_opm": -100.0,
    "max_pe": 500.0,
    "max_pb": 100.0,
    "min_dividend_yield": -100.0,
    "min_icr": -100.0,
}


if preset != "Custom":
    defaults = get_preset_values(preset)


# ------------------------------------------------------------------
# Screener Filters
# ------------------------------------------------------------------

st.sidebar.subheader("Screener Filters")


# ------------------------------------------------------------------
# ROE
# ------------------------------------------------------------------

min_roe = st.sidebar.slider(
    "ROE minimum (%)",
    min_value=-100.0,
    max_value=100.0,
    value=float(defaults["min_roe"]),
    step=1.0,
)


# ------------------------------------------------------------------
# Debt / Equity
# ------------------------------------------------------------------

max_de = st.sidebar.slider(
    "D/E maximum",
    min_value=0.0,
    max_value=100.0,
    value=float(
        min(defaults["max_de"], 100.0)
    ),
    step=0.1,
)


# ------------------------------------------------------------------
# Free Cash Flow
# ------------------------------------------------------------------

min_fcf = st.sidebar.number_input(
    "FCF minimum (₹ Cr)",
    value=float(defaults["min_fcf"]),
)


# ------------------------------------------------------------------
# Revenue CAGR
# ------------------------------------------------------------------

min_revenue_cagr = st.sidebar.slider(
    "Revenue CAGR minimum (%)",
    min_value=-100.0,
    max_value=100.0,
    value=float(
        max(-100.0, defaults["min_revenue_cagr"])
    ),
    step=1.0,
)


# ------------------------------------------------------------------
# PAT CAGR
# ------------------------------------------------------------------

min_pat_cagr = st.sidebar.slider(
    "PAT CAGR minimum (%)",
    min_value=-100.0,
    max_value=100.0,
    value=float(
        max(-100.0, defaults["min_pat_cagr"])
    ),
    step=1.0,
)


# ------------------------------------------------------------------
# Operating Profit Margin
# ------------------------------------------------------------------

min_opm = st.sidebar.slider(
    "OPM minimum (%)",
    min_value=-100.0,
    max_value=100.0,
    value=float(
        max(-100.0, defaults["min_opm"])
    ),
    step=1.0,
)


# ------------------------------------------------------------------
# P/E
# ------------------------------------------------------------------

max_pe = st.sidebar.slider(
    "P/E maximum",
    min_value=0.0,
    max_value=500.0,
    value=float(
        min(defaults["max_pe"], 500.0)
    ),
    step=1.0,
)


# ------------------------------------------------------------------
# P/B
# ------------------------------------------------------------------

max_pb = st.sidebar.slider(
    "P/B maximum",
    min_value=0.0,
    max_value=100.0,
    value=float(
        min(defaults["max_pb"], 100.0)
    ),
    step=0.1,
)


# ------------------------------------------------------------------
# Dividend Yield
# ------------------------------------------------------------------

min_dividend_yield = st.sidebar.slider(
    "Dividend Yield minimum (%)",
    min_value=-100.0,
    max_value=20.0,
    value=float(
        min(defaults["min_dividend_yield"], 20.0)
    ),
    step=0.5,
)


# ------------------------------------------------------------------
# Interest Coverage
# ------------------------------------------------------------------

min_icr = st.sidebar.slider(
    "Interest Coverage minimum",
    min_value=-100.0,
    max_value=100.0,
    value=float(
        min(defaults["min_icr"], 100.0)
    ),
    step=1.0,
)


# ------------------------------------------------------------------
# Apply Filters
# ------------------------------------------------------------------

filtered = apply_screener_filters(
    df=df,
    min_roe=min_roe,
    max_de=max_de,
    min_fcf=min_fcf,
    min_revenue_cagr=min_revenue_cagr,
    min_pat_cagr=min_pat_cagr,
    min_opm=min_opm,
    max_pe=max_pe,
    max_pb=max_pb,
    min_dividend_yield=min_dividend_yield,
    min_icr=min_icr,
)


# ------------------------------------------------------------------
# Result Count
# ------------------------------------------------------------------

st.subheader(
    f"{len(filtered)} companies match your filters"
)


# ------------------------------------------------------------------
# Results Table
# ------------------------------------------------------------------

available_display_columns = [
    column
    for column in DISPLAY_COLUMNS
    if column in filtered.columns
]

display_df = filtered[
    available_display_columns
].copy()


display_df = display_df.rename(
    columns={
        "company_id": "Company ID",
        "company_name": "Company Name",
        "broad_sector": "Sector",
        "composite_quality_score": "Composite Score",
        "return_on_equity_pct": "ROE (%)",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "Free Cash Flow",
        "revenue_cagr_5y": "Revenue CAGR (5Y)",
        "pat_cagr_5y": "PAT CAGR (5Y)",
        "operating_profit_margin_pct": "OPM (%)",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Dividend Yield (%)",
        "interest_coverage": "Interest Coverage",
    }
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# ------------------------------------------------------------------
# CSV Download
# ------------------------------------------------------------------

csv_data = display_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Screener CSV",
    data=csv_data,
    file_name=(
        f"screener_{int(selected_year)}.csv"
    ),
    mime="text/csv",
)


# ------------------------------------------------------------------
# Missing Data Note
# ------------------------------------------------------------------

if display_df.isna().any().any():
    st.caption(
        "Note: N/A values indicate that the corresponding metric "
        "is unavailable for that company/year."
    )