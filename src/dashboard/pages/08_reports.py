from pathlib import Path

import streamlit as st


# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Reports | Nifty 100 Analytics",
    layout="wide",
)


# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
INSIGHTS_DIR = PROJECT_ROOT / "reports" / "executive_insights"
RADAR_DIR = PROJECT_ROOT / "reports" / "radar_charts"


# ------------------------------------------------------------------
# Page Header
# ------------------------------------------------------------------

st.title("📑 Reports & Insights")

st.caption(
    "Explore generated executive insights, financial radar charts "
    "and analytical output files from the Nifty 100 Financial "
    "Intelligence Platform."
)


# ------------------------------------------------------------------
# Verify Directories
# ------------------------------------------------------------------

if not OUTPUTS_DIR.exists():
    st.error(
        f"Outputs directory not found: {OUTPUTS_DIR}"
    )

if not INSIGHTS_DIR.exists():
    st.error(
        f"Executive insights directory not found: {INSIGHTS_DIR}"
    )

if not RADAR_DIR.exists():
    st.error(
        f"Radar charts directory not found: {RADAR_DIR}"
    )


# ------------------------------------------------------------------
# Collect Existing Files
# ------------------------------------------------------------------

insight_files = sorted(
    [
        file
        for file in INSIGHTS_DIR.glob("*_insights.txt")
        if file.is_file()
    ],
    key=lambda file: file.stem,
)

radar_files = sorted(
    [
        file
        for file in RADAR_DIR.glob("*_radar.png")
        if file.is_file()
    ],
    key=lambda file: file.stem,
)

output_files = sorted(
    [
        file
        for file in OUTPUTS_DIR.iterdir()
        if file.is_file()
        and file.name != ".gitkeep"
    ],
    key=lambda file: file.name.lower(),
)


# ------------------------------------------------------------------
# Summary Metrics
# ------------------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Executive Insights",
        len(insight_files),
    )

with col2:
    st.metric(
        "Radar Charts",
        len(radar_files),
    )

with col3:
    st.metric(
        "Output Files",
        len(output_files),
    )


st.divider()


# ==================================================================
# EXECUTIVE INSIGHTS
# ==================================================================

st.header("🧠 Executive Insights")

st.caption(
    "Generated company-level financial insights from the analytics "
    "pipeline."
)


if not insight_files:

    st.info(
        "No executive insight reports have been generated yet."
    )

else:

    insight_companies = {
        file.stem.replace("_insights", ""): file
        for file in insight_files
    }

    selected_insight_company = st.selectbox(
        "Select Company",
        sorted(insight_companies.keys()),
        key="insight_company",
    )

    selected_insight_file = insight_companies[
        selected_insight_company
    ]

    try:

        insight_text = selected_insight_file.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        insight_text = selected_insight_file.read_text(
            encoding="latin-1"
        )

    st.subheader(
        f"{selected_insight_company} — Executive Insight"
    )

    st.text_area(
        "Generated Insight",
        value=insight_text,
        height=350,
        disabled=True,
    )

    st.download_button(
        label="⬇️ Download Executive Insight",
        data=insight_text.encode("utf-8"),
        file_name=selected_insight_file.name,
        mime="text/plain",
        key="download_insight",
    )


st.divider()


# ==================================================================
# RADAR CHARTS
# ==================================================================

st.header("📊 Financial Radar Charts")

st.caption(
    "Pre-generated financial health and performance radar charts "
    "for companies in the reporting dataset."
)

if not radar_files:

    st.info(
        "No radar charts have been generated yet."
    )

else:

    radar_companies = {
        file.stem.replace("_radar", ""): file
        for file in radar_files
    }

    selected_radar_company = st.selectbox(
        "Select Company",
        sorted(radar_companies.keys()),
        key="radar_company",
    )

    selected_radar_file = radar_companies[
        selected_radar_company
    ]

    st.subheader(
        f"{selected_radar_company} — Financial Radar"
    )

    # --------------------------------------------------------------
    # Centered Radar Chart
    # --------------------------------------------------------------

    _, radar_col, _ = st.columns([1, 2, 1])

    with radar_col:
        st.image(
            str(selected_radar_file),
            width=750,
        )

    # --------------------------------------------------------------
    # Download Radar Chart
    # --------------------------------------------------------------

    with open(
        selected_radar_file,
        "rb",
    ) as file:

        radar_bytes = file.read()

    st.download_button(
        label="⬇️ Download Radar Chart",
        data=radar_bytes,
        file_name=selected_radar_file.name,
        mime="image/png",
        key="download_radar",
    )

st.divider()


# ==================================================================
# ANALYTICAL OUTPUTS
# ==================================================================

st.header("📦 Analytical Outputs")

st.caption(
    "Source files and analytical outputs generated by the project "
    "pipeline."
)


if not output_files:

    st.info(
        "No analytical output files are currently available."
    )

else:

    for output_file in output_files:

        extension = output_file.suffix.lower()

        if extension == ".xlsx":
            file_type = "Excel workbook"
            mime_type = (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )

        elif extension == ".csv":
            file_type = "CSV dataset"
            mime_type = "text/csv"

        elif extension == ".log":
            file_type = "Log file"
            mime_type = "text/plain"

        else:
            file_type = "Output file"
            mime_type = "application/octet-stream"

        file_size_kb = output_file.stat().st_size / 1024

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [5, 2, 2]
            )

            with col1:

                st.markdown(
                    f"**{output_file.name}**"
                )

                st.caption(
                    f"{file_type} • "
                    f"{file_size_kb:.1f} KB"
                )

            with col2:

                st.write("Available")

            with col3:

                with open(
                    output_file,
                    "rb",
                ) as file:

                    output_bytes = file.read()

                st.download_button(
                    label="⬇️ Download",
                    data=output_bytes,
                    file_name=output_file.name,
                    mime=mime_type,
                    key=f"download_{output_file.name}",
                )


st.divider()


# ==================================================================
# REPORT COVERAGE
# ==================================================================

st.header("📌 Report Coverage")

insight_company_set = set(
    insight_companies.keys()
    if insight_files
    else []
)

radar_company_set = set(
    radar_companies.keys()
    if radar_files
    else []
)

all_report_companies = sorted(
    insight_company_set | radar_company_set
)


if not all_report_companies:

    st.info(
        "No company-level reports are currently available."
    )

else:

    coverage_data = []

    for company in all_report_companies:

        coverage_data.append(
            {
                "Company": company,
                "Executive Insight": (
                    "Available"
                    if company in insight_company_set
                    else "Not Available"
                ),
                "Radar Chart": (
                    "Available"
                    if company in radar_company_set
                    else "Not Available"
                ),
            }
        )

    st.dataframe(
        coverage_data,
        use_container_width=True,
        hide_index=True,
    )


# ------------------------------------------------------------------
# Footer
# ------------------------------------------------------------------

st.caption(
    "Reports shown here are existing artifacts generated by the "
    "Nifty 100 analytics pipeline. No reports are regenerated by "
    "the dashboard."
)