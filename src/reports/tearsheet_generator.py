"""
Sprint 5 — Tearsheet Generator

Generates one-page financial intelligence PDF tearsheets
for the official 92-company universe.

Inputs:
    data/nifty100.db
    outputs/cashflow_intelligence.xlsx
    outputs/capital_allocation_distribution.csv
    outputs/pattern_changes.csv

Output:
    reports/tearsheets/<COMPANY_ID>_tearsheet.pdf

The generator is read-only with respect to the database and
existing analytics outputs.
"""

from pathlib import Path
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

DB_PATH = Path("data/nifty100.db")

CASHFLOW_FILE = Path(
    "outputs/cashflow_intelligence.xlsx"
)

OUTPUT_DIR = Path(
    "reports/tearsheets"
)

EXPECTED_COMPANIES = 92


# ------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------

def safe_value(value, default="N/A"):
    """
    Convert missing/empty values into a readable display value.
    """

    if pd.isna(value):
        return default

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return default

    return value


def format_number(value, decimals=2):
    """
    Format numeric values for PDF display.
    """

    if pd.isna(value):
        return "N/A"

    try:

        number = float(value)

    except (TypeError, ValueError):

        return str(value)

    return f"{number:,.{decimals}f}"


def format_percent(value, decimals=2):
    """
    Format a percentage value.
    """

    if pd.isna(value):
        return "N/A"

    try:

        number = float(value)

    except (TypeError, ValueError):

        return str(value)

    return f"{number:.{decimals}f}%"


def format_flag(value):
    """
    Format boolean-style intelligence flags.
    """

    if pd.isna(value):
        return "N/A"

    if isinstance(value, str):

        text = value.strip().lower()

        if text in {"true", "yes", "1", "y"}:
            return "Yes"

        if text in {"false", "no", "0", "n"}:
            return "No"

    if value in [True, 1]:
        return "Yes"

    if value in [False, 0]:
        return "No"

    return str(value)


def latest_record(df, company_id):
    """
    Return the latest available record for a company.
    """

    company_data = df[
        df["company_id"] == company_id
    ].copy()

    if company_data.empty:
        return None

    if "year" in company_data.columns:

        company_data["year"] = pd.to_numeric(
            company_data["year"],
            errors="coerce",
        )

        company_data = company_data.sort_values(
            "year"
        )

    return company_data.iloc[-1]


def safe_text(text, max_length=500):
    """
    Prepare longer text fields for PDF display.
    """

    if pd.isna(text):
        return "N/A"

    text = str(text).strip()

    if not text:
        return "N/A"

    if len(text) > max_length:
        text = text[:max_length].rstrip() + "..."

    return text


# ------------------------------------------------------------------
# Database loading
# ------------------------------------------------------------------

def load_database_data():
    """
    Load all required database tables.
    """

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)

    try:

        companies = pd.read_sql_query(
            """
            SELECT
                id AS company_id,
                company_name,
                about_company,
                website,
                face_value,
                book_value,
                roce_percentage,
                roe_percentage
            FROM companies
            ORDER BY id
            """,
            connection,
        )

        profit_loss = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                sales,
                operating_profit,
                opm_percentage,
                profit_before_tax,
                net_profit,
                eps,
                dividend_payout
            FROM profitandloss
            """,
            connection,
        )

        balance_sheet = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                reserves,
                borrowings,
                total_liabilities,
                fixed_assets,
                investments,
                total_assets
            FROM balancesheet
            """,
            connection,
        )

        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                net_profit_margin_pct,
                operating_profit_margin_pct,
                return_on_equity_pct,
                debt_to_equity,
                interest_coverage,
                asset_turnover,
                free_cash_flow_cr,
                capex_cr,
                earnings_per_share,
                book_value_per_share,
                dividend_payout_ratio_pct,
                total_debt_cr,
                cash_from_operations_cr
            FROM financial_ratios
            """,
            connection,
        )

        pros_cons = pd.read_sql_query(
            """
            SELECT
                company_id,
                pros,
                cons
            FROM prosandcons
            """,
            connection,
        )

    finally:

        connection.close()

    return (
        companies,
        profit_loss,
        balance_sheet,
        ratios,
        pros_cons,
    )


# ------------------------------------------------------------------
# Cash-flow intelligence loading
# ------------------------------------------------------------------

def load_cashflow_intelligence():
    """
    Load the existing Day 31 cash-flow intelligence output.
    """

    if not CASHFLOW_FILE.exists():

        raise FileNotFoundError(
            "Cash-flow intelligence file not found: "
            f"{CASHFLOW_FILE}"
        )

    sheets = pd.ExcelFile(
        CASHFLOW_FILE
    )

    if not sheets.sheet_names:

        raise ValueError(
            "Cash-flow intelligence Excel contains no sheets."
        )

    data = pd.read_excel(
        CASHFLOW_FILE,
        sheet_name=sheets.sheet_names[0],
    )

    required_columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:

        raise ValueError(
            "Cash-flow intelligence output is missing "
            "required columns: "
            + ", ".join(missing)
        )

    return data


# ------------------------------------------------------------------
# PDF styles
# ------------------------------------------------------------------

def create_styles():
    """
    Create report styles.
    """

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="TearsheetTitle",
            parent=styles["Title"],
            fontSize=17,
            leading=20,
            alignment=TA_LEFT,
            spaceAfter=3 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CompanySubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#555555"),
            spaceAfter=4 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontSize=10,
            leading=12,
            textColor=colors.white,
            backColor=colors.HexColor("#1F4E78"),
            leftIndent=0,
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
            borderPadding=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallText",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9.5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            fontSize=6.5,
            leading=8,
            textColor=colors.HexColor("#666666"),
            alignment=TA_CENTER,
        )
    )

    return styles


# ------------------------------------------------------------------
# Table helpers
# ------------------------------------------------------------------

def make_kpi_table(rows):
    """
    Create a compact KPI table.
    """

    table = Table(
        rows,
        colWidths=[
            42 * mm,
            42 * mm,
            42 * mm,
            42 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#D9EAF7"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1F1F1F"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#BBBBBB"),
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


def make_two_column_table(rows):
    """
    Create a two-column information table.
    """

    table = Table(
        rows,
        colWidths=[
            58 * mm,
            110 * mm,
        ],
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor("#CCCCCC"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#F2F2F2"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    return table


# ------------------------------------------------------------------
# Single-company PDF
# ------------------------------------------------------------------

def build_tearsheet(
    company,
    profit_loss,
    balance_sheet,
    ratios,
    pros_cons,
    cashflow_intelligence,
    styles,
    output_path,
):
    """
    Generate a single company tearsheet.
    """

    company_id = company["company_id"]

    company_pl = profit_loss[
        profit_loss["company_id"] == company_id
    ].copy()

    company_bs = balance_sheet[
        balance_sheet["company_id"] == company_id
    ].copy()

    company_ratios = ratios[
        ratios["company_id"] == company_id
    ].copy()

    intelligence = cashflow_intelligence[
        cashflow_intelligence["company_id"]
        == company_id
    ].copy()

    company_pros_cons = pros_cons[
        pros_cons["company_id"] == company_id
    ].copy()

    latest_pl = latest_record(
        company_pl,
        company_id,
    )

    latest_bs = latest_record(
        company_bs,
        company_id,
    )

    latest_ratio = latest_record(
        company_ratios,
        company_id,
    )

    latest_intelligence = latest_record(
        intelligence,
        company_id,
    )

    if latest_pl is not None:
        latest_pl_year = safe_value(
            latest_pl.get("year")
        )
    else:
        latest_pl_year = "N/A"

    if latest_bs is not None:
        latest_bs_year = safe_value(
            latest_bs.get("year")
        )
    else:
        latest_bs_year = "N/A"

    if latest_ratio is not None:
        latest_ratio_year = safe_value(
            latest_ratio.get("year")
        )
    else:
        latest_ratio_year = "N/A"

    # --------------------------------------------------------------
    # Document
    # --------------------------------------------------------------

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    story = []

    # --------------------------------------------------------------
    # Header
    # --------------------------------------------------------------

    company_name = safe_value(
        company.get("company_name"),
        company_id,
    )

    story.append(
        Paragraph(
            f"{company_id} — {company_name}",
            styles["TearsheetTitle"],
        )
    )

    story.append(
        Paragraph(
            "N100 Financial Intelligence Platform | "
            "Company Intelligence Tearsheet",
            styles["CompanySubtitle"],
        )
    )

    # --------------------------------------------------------------
    # Company profile
    # --------------------------------------------------------------

    story.append(
        Paragraph(
            "Company Profile",
            styles["SectionHeader"],
        )
    )

    profile_rows = [
        [
            "Company ID",
            company_id,
        ],
        [
            "Company Name",
            company_name,
        ],
        [
            "Latest P&L Year",
            latest_pl_year,
        ],
        [
            "Latest Balance Sheet Year",
            latest_bs_year,
        ],
        [
            "Latest Ratio Year",
            latest_ratio_year,
        ],
        [
            "Face Value",
            format_number(
                company.get("face_value")
            ),
        ],
        [
            "Book Value",
            format_number(
                company.get("book_value")
            ),
        ],
        [
            "ROCE",
            format_percent(
                company.get("roce_percentage")
            ),
        ],
        [
            "ROE",
            format_percent(
                company.get("roe_percentage")
            ),
        ],
    ]

    story.append(
        make_two_column_table(
            profile_rows
        )
    )

    # --------------------------------------------------------------
    # Core financial KPIs
    # --------------------------------------------------------------

    story.append(
        Paragraph(
            "Core Financial KPIs",
            styles["SectionHeader"],
        )
    )

    if latest_pl is not None:

        sales = format_number(
            latest_pl.get("sales")
        )

        operating_profit = format_number(
            latest_pl.get("operating_profit")
        )

        opm = format_percent(
            latest_pl.get("opm_percentage")
        )

        net_profit = format_number(
            latest_pl.get("net_profit")
        )

        eps = format_number(
            latest_pl.get("eps")
        )

        dividend = format_percent(
            latest_pl.get("dividend_payout")
        )

    else:

        sales = "N/A"
        operating_profit = "N/A"
        opm = "N/A"
        net_profit = "N/A"
        eps = "N/A"
        dividend = "N/A"

    kpi_rows = [
        [
            "Sales",
            "Operating Profit",
            "Operating Margin",
            "Net Profit",
        ],
        [
            sales,
            operating_profit,
            opm,
            net_profit,
        ],
        [
            "EPS",
            "Dividend Payout",
            "ROE",
            "ROCE",
        ],
        [
            (
                eps
            ),
            dividend,
            format_percent(
                company.get("roe_percentage")
            ),
            format_percent(
                company.get("roce_percentage")
            ),
        ],
    ]

    story.append(
        make_kpi_table(
            kpi_rows
        )
    )

    # --------------------------------------------------------------
    # Balance sheet
    # --------------------------------------------------------------

    story.append(
        Paragraph(
            "Balance Sheet & Leverage",
            styles["SectionHeader"],
        )
    )

    if latest_bs is not None:

        balance_rows = [
            [
                "Borrowings",
                format_number(
                    latest_bs.get(
                        "borrowings"
                    )
                ),
            ],
            [
                "Reserves",
                format_number(
                    latest_bs.get(
                        "reserves"
                    )
                ),
            ],
            [
                "Total Assets",
                format_number(
                    latest_bs.get(
                        "total_assets"
                    )
                ),
            ],
            [
                "Fixed Assets",
                format_number(
                    latest_bs.get(
                        "fixed_assets"
                    )
                ),
            ],
            [
                "Investments",
                format_number(
                    latest_bs.get(
                        "investments"
                    )
                ),
            ],
        ]

    else:

        balance_rows = [
            ["Borrowings", "N/A"],
            ["Reserves", "N/A"],
            ["Total Assets", "N/A"],
            ["Fixed Assets", "N/A"],
            ["Investments", "N/A"],
        ]

    if latest_ratio is not None:

        balance_rows.extend(
            [
                [
                    "Debt / Equity",
                    format_number(
                        latest_ratio.get(
                            "debt_to_equity"
                        )
                    ),
                ],
                [
                    "Interest Coverage",
                    format_number(
                        latest_ratio.get(
                            "interest_coverage"
                        )
                    ),
                ],
                [
                    "Total Debt",
                    format_number(
                        latest_ratio.get(
                            "total_debt_cr"
                        )
                    ),
                ],
            ]
        )

    story.append(
        make_two_column_table(
            balance_rows
        )
    )

    # --------------------------------------------------------------
    # Cash-flow intelligence
    # --------------------------------------------------------------

    story.append(
        Paragraph(
            "Cash-Flow Intelligence",
            styles["SectionHeader"],
        )
    )

    if latest_intelligence is not None:

        intelligence_rows = [
            [
                "CFO Quality",
                (
                    f"{format_number(latest_intelligence.get('cfo_quality_score'))} "
                    f"({safe_value(latest_intelligence.get('cfo_quality_label'))})"
                ),
            ],
            [
                "Capex Intensity",
                (
                    f"{format_percent(latest_intelligence.get('capex_intensity_pct'))} "
                    f"({safe_value(latest_intelligence.get('capex_label'))})"
                ),
            ],
            [
                "FCF CAGR — 5Y",
                format_percent(
                    latest_intelligence.get(
                        "fcf_cagr_5yr"
                    )
                ),
            ],
            [
                "FCF Conversion",
                format_percent(
                    latest_intelligence.get(
                        "fcf_conversion_pct"
                    )
                ),
            ],
            [
                "Distress Flag",
                format_flag(
                    latest_intelligence.get(
                        "distress_flag"
                    )
                ),
            ],
            [
                "Deleveraging Flag",
                format_flag(
                    latest_intelligence.get(
                        "deleveraging_flag"
                    )
                ),
            ],
            [
                "Capital Allocation",
                safe_value(
                    latest_intelligence.get(
                        "capital_allocation_label"
                    )
                ),
            ],
        ]

        if "sector" in latest_intelligence.index:

            intelligence_rows.insert(
                0,
                [
                    "Sector",
                    safe_value(
                        latest_intelligence.get(
                            "sector"
                        )
                    ),
                ],
            )

    else:

        intelligence_rows = [
            [
                "Cash-Flow Intelligence",
                "Not available",
            ]
        ]

    story.append(
        make_two_column_table(
            intelligence_rows
        )
    )

    # --------------------------------------------------------------
    # Ratio snapshot
    # --------------------------------------------------------------

    story.append(
        Paragraph(
            "Financial Ratio Snapshot",
            styles["SectionHeader"],
        )
    )

    if latest_ratio is not None:

        ratio_rows = [
            [
                "Net Profit Margin",
                format_percent(
                    latest_ratio.get(
                        "net_profit_margin_pct"
                    )
                ),
            ],
            [
                "Operating Profit Margin",
                format_percent(
                    latest_ratio.get(
                        "operating_profit_margin_pct"
                    )
                ),
            ],
            [
                "Return on Equity",
                format_percent(
                    latest_ratio.get(
                        "return_on_equity_pct"
                    )
                ),
            ],
            [
                "Debt / Equity",
                format_number(
                    latest_ratio.get(
                        "debt_to_equity"
                    )
                ),
            ],
            [
                "Interest Coverage",
                format_number(
                    latest_ratio.get(
                        "interest_coverage"
                    )
                ),
            ],
            [
                "Asset Turnover",
                format_number(
                    latest_ratio.get(
                        "asset_turnover"
                    )
                ),
            ],
            [
                "Free Cash Flow",
                format_number(
                    latest_ratio.get(
                        "free_cash_flow_cr"
                    )
                ),
            ],
            [
                "Capex",
                format_number(
                    latest_ratio.get(
                        "capex_cr"
                    )
                ),
            ],
        ]

    else:

        ratio_rows = [
            [
                "Financial Ratios",
                "Not available",
            ]
        ]

    story.append(
        make_two_column_table(
            ratio_rows
        )
    )

    # --------------------------------------------------------------
    # Pros & cons
    # --------------------------------------------------------------

    story.append(
        Paragraph(
            "Business Signals",
            styles["SectionHeader"],
        )
    )

    if not company_pros_cons.empty:

        row = company_pros_cons.iloc[0]

        pros = safe_text(
            row.get("pros"),
            700,
        )

        cons = safe_text(
            row.get("cons"),
            700,
        )

    else:

        pros = "Not available"
        cons = "Not available"

    business_rows = [
        [
            "Pros",
            Paragraph(
                pros,
                styles["SmallText"],
            ),
        ],
        [
            "Cons",
            Paragraph(
                cons,
                styles["SmallText"],
            ),
        ],
    ]

    story.append(
        make_two_column_table(
            business_rows
        )
    )

    # --------------------------------------------------------------
    # About company
    # --------------------------------------------------------------

    about = safe_text(
        company.get("about_company"),
        900,
    )

    if about != "N/A":

        story.append(
            Paragraph(
                "Company Overview",
                styles["SectionHeader"],
            )
        )

        story.append(
            Paragraph(
                about,
                styles["BodySmall"],
            )
        )

    # --------------------------------------------------------------
    # Footer
    # --------------------------------------------------------------

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    story.append(
        Paragraph(
            "Generated by N100 Financial Intelligence Platform | "
            "Analytical output for research and screening purposes.",
            styles["Footer"],
        )
    )

    document.build(
        story
    )


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------

def validate_inputs(
    companies,
    cashflow_intelligence,
):
    """
    Validate the official universe before generation.
    """

    company_count = companies[
        "company_id"
    ].nunique()

    if company_count != EXPECTED_COMPANIES:

        raise ValueError(
            "Expected "
            f"{EXPECTED_COMPANIES} companies but found "
            f"{company_count}."
        )

    intelligence_ids = set(
        cashflow_intelligence[
            "company_id"
        ]
        .dropna()
        .unique()
    )

    official_ids = set(
        companies[
            "company_id"
        ]
    )

    missing_intelligence = (
        official_ids - intelligence_ids
    )

    if missing_intelligence:

        print(
            "WARNING — Companies missing "
            "cash-flow intelligence:"
        )

        print(
            ", ".join(
                sorted(
                    missing_intelligence
                )
            )
        )


# ------------------------------------------------------------------
# Main generator
# ------------------------------------------------------------------

def generate():
    """
    Generate tearsheets for all official companies.
    """

    print("=" * 72)
    print(
        "SPRINT 5 — FINANCIAL INTELLIGENCE TEARSHEET GENERATOR"
    )
    print("=" * 72)

    # --------------------------------------------------------------
    # Load database
    # --------------------------------------------------------------

    print("\nLoading database data...")

    (
        companies,
        profit_loss,
        balance_sheet,
        ratios,
        pros_cons,
    ) = load_database_data()

    print(
        f"Companies loaded       : "
        f"{companies['company_id'].nunique()}"
    )

    # --------------------------------------------------------------
    # Load cash-flow intelligence
    # --------------------------------------------------------------

    print(
        "\nLoading cash-flow intelligence..."
    )

    cashflow_intelligence = (
        load_cashflow_intelligence()
    )

    print(
        f"Cash-flow records      : "
        f"{len(cashflow_intelligence)}"
    )

    # --------------------------------------------------------------
    # Validate
    # --------------------------------------------------------------

    validate_inputs(
        companies,
        cashflow_intelligence,
    )

    # --------------------------------------------------------------
    # Prepare output directory
    # --------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------------
    # Styles
    # --------------------------------------------------------------

    styles = create_styles()

    # --------------------------------------------------------------
    # Generate PDFs
    # --------------------------------------------------------------

    generated = 0
    failed = []

    for _, company in companies.iterrows():

        company_id = company[
            "company_id"
        ]

        output_path = (
            OUTPUT_DIR
            / f"{company_id}_tearsheet.pdf"
        )

        try:

            build_tearsheet(
                company=company,
                profit_loss=profit_loss,
                balance_sheet=balance_sheet,
                ratios=ratios,
                pros_cons=pros_cons,
                cashflow_intelligence=(
                    cashflow_intelligence
                ),
                styles=styles,
                output_path=output_path,
            )

            generated += 1

            print(
                f"[{generated:>2}/{len(companies)}] "
                f"Generated {output_path.name}"
            )

        except Exception as error:

            failed.append(
                (
                    company_id,
                    str(error),
                )
            )

            print(
                f"[ERROR] {company_id}: {error}"
            )

    # --------------------------------------------------------------
    # Final report
    # --------------------------------------------------------------

    print("\n" + "=" * 72)
    print(
        "TEARSHEET GENERATION COMPLETED"
    )
    print("=" * 72)

    print(
        f"Official companies : "
        f"{len(companies)}"
    )

    print(
        f"PDFs generated     : "
        f"{generated}"
    )

    print(
        f"Failed             : "
        f"{len(failed)}"
    )

    print(
        f"Output directory   : "
        f"{OUTPUT_DIR}"
    )

    if failed:

        print(
            "\nFailed companies:"
        )

        for company_id, error in failed:

            print(
                f"  {company_id}: {error}"
            )

    else:

        print(
            "\nSTATUS: PASS"
        )

    print("=" * 72)

    return generated, failed


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    generate()