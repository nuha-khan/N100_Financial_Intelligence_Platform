"""
Sprint 5 — Day 35 Portfolio Summary PDF

Generates:
    reports/portfolio/portfolio_summary.pdf

Contents:
    - One page per company
    - All 92 companies
    - Alphabetical order by ticker
    - Company name and sector
    - Top 6 KPIs consistent with the Day 33 tearsheet:
        Revenue
        Net Profit
        ROE
        ROCE
        Book Value
        Face Value
    - 3-year trend arrows:
        ↑ = improved
        ↓ = declined
        → = flat within 2%
    - Missing historical data is handled safely

The report uses the same ReportLab styling conventions as the
existing Day 33/34 reports.
"""

from pathlib import Path
import sqlite3

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path("data/nifty100.db")

REPORTS_DIR = Path("reports")
PORTFOLIO_DIR = REPORTS_DIR / "portfolio"

OUTPUT_FILE = PORTFOLIO_DIR / "portfolio_summary.pdf"

EXPECTED_COMPANIES = 92

# Flat if the latest value is within ±2% of the comparison value.
FLAT_THRESHOLD = 0.02


# ============================================================================
# COLORS
# ============================================================================

NAVY = colors.HexColor("#17365D")
LIGHT_BLUE = colors.HexColor("#D9EAF7")
VERY_LIGHT_BLUE = colors.HexColor("#F4F8FB")
BORDER = colors.HexColor("#C7D1DB")
DARK_TEXT = colors.HexColor("#222222")
GREY_TEXT = colors.HexColor("#666666")
WHITE = colors.white

GREEN = colors.HexColor("#2E7D32")
LIGHT_GREEN = colors.HexColor("#E8F5E9")

RED = colors.HexColor("#C62828")
LIGHT_RED = colors.HexColor("#FFEBEE")


# ============================================================================
# DATABASE LOADING
# ============================================================================

def load_portfolio_data():
    """Load datasets required for the Day 35 portfolio summary."""

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
                roe_percentage,
                roce_percentage,
                book_value,
                face_value
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
                net_profit
            FROM profitandloss
            """,
            connection,
        )

        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                return_on_equity_pct
            FROM financial_ratios
            """,
            connection,
        )

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector
            FROM sectors
            """,
            connection,
        )

    finally:
        connection.close()

    return (
        companies,
        profit_loss,
        ratios,
        sectors,
    )


# ============================================================================
# GENERAL HELPERS
# ============================================================================

def safe_value(value, default="N/A"):
    """Return a safe display value."""

    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return default

    return value


def safe_number(value, decimals=2):
    """Format a numeric value."""

    try:
        if pd.isna(value):
            return "N/A"

        return f"{float(value):,.{decimals}f}"

    except (TypeError, ValueError):
        return "N/A"


def safe_percentage(value, decimals=2):
    """Format a percentage value."""

    try:
        if pd.isna(value):
            return "N/A"

        return f"{float(value):.{decimals}f}%"

    except (TypeError, ValueError):
        return "N/A"


def prepare_year_data(df):
    """Convert year to numeric and sort chronologically."""

    result = df.copy()

    if result.empty:
        return result

    if "year" not in result.columns:
        return result

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce",
    )

    result = result.dropna(
        subset=["year"]
    )

    if result.empty:
        return result

    result["year"] = result["year"].astype(int)

    return result.sort_values("year")


def latest_row(df):
    """Return the latest available row."""

    prepared = prepare_year_data(df)

    if prepared.empty:
        return None

    return prepared.iloc[-1]


def get_three_year_comparison(df):
    """
    Return latest and approximately three-years-prior values.

    The comparison uses the latest available year and the latest
    record at least two years before it. This accommodates gaps
    in company financial histories.
    """

    prepared = prepare_year_data(df)

    if prepared.empty:
        return None, None

    latest = prepared.iloc[-1]

    latest_year = latest["year"]

    historical = prepared[
        prepared["year"] <= latest_year - 2
    ]

    if historical.empty:
        return latest, None

    previous = historical.iloc[-1]

    return latest, previous


# ============================================================================
# TREND LOGIC
# ============================================================================

def trend_arrow(latest, previous):
    """
    Determine 3-year trend.

    ↑ = improved by more than 2%
    ↓ = declined by more than 2%
    → = within ±2%

    For unavailable historical values, → is used because no
    directional movement can be established.
    """

    try:
        if pd.isna(latest) or pd.isna(previous):
            return "→"

        latest = float(latest)
        previous = float(previous)

    except (TypeError, ValueError):
        return "→"

    if previous == 0:
        if latest > 0:
            return "↑"

        if latest < 0:
            return "↓"

        return "→"

    change = (latest - previous) / abs(previous)

    if change > FLAT_THRESHOLD:
        return "↑"

    if change < -FLAT_THRESHOLD:
        return "↓"

    return "→"


def trend_text(arrow):
    """Return a readable trend label."""

    if arrow == "↑":
        return "Improved"

    if arrow == "↓":
        return "Declined"

    return "Flat"


# ============================================================================
# REPORT STYLES
# ============================================================================

def create_styles():
    """Create ReportLab styles."""

    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "PortfolioTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=21,
            textColor=WHITE,
            alignment=TA_LEFT,
        ),

        "subtitle": ParagraphStyle(
            "PortfolioSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#DDE7F0"),
        ),

        "section": ParagraphStyle(
            "PortfolioSection",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=WHITE,
            backColor=NAVY,
            borderPadding=4,
            spaceBefore=2 * mm,
            spaceAfter=2 * mm,
        ),

        "kpi_label": ParagraphStyle(
            "PortfolioKPILabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8,
            textColor=GREY_TEXT,
            alignment=TA_CENTER,
        ),

        "kpi_value": ParagraphStyle(
            "PortfolioKPIValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),

        "trend": ParagraphStyle(
            "PortfolioTrend",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=13,
            alignment=TA_CENTER,
        ),

        "body": ParagraphStyle(
            "PortfolioBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=DARK_TEXT,
        ),

        "small": ParagraphStyle(
            "PortfolioSmall",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            textColor=GREY_TEXT,
        ),

        "footer": ParagraphStyle(
            "PortfolioFooter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            alignment=TA_CENTER,
            textColor=GREY_TEXT,
        ),
    }


# ============================================================================
# COMPANY DATA PREPARATION
# ============================================================================

def prepare_company_summary(
    company,
    profit_loss,
    ratios,
    sectors,
):
    """Prepare all Day 35 information for one company."""

    company_id = company["company_id"]

    company_pl = profit_loss[
        profit_loss["company_id"] == company_id
    ].copy()

    company_ratios = ratios[
        ratios["company_id"] == company_id
    ].copy()

    sector_match = sectors[
        sectors["company_id"] == company_id
    ]

    if sector_match.empty:
        sector = "N/A"
    else:
        sector = safe_value(
            sector_match.iloc[0]["broad_sector"]
        )

    latest_pl, previous_pl = get_three_year_comparison(
        company_pl
    )

    latest_ratio, previous_ratio = get_three_year_comparison(
        company_ratios
    )

    if latest_pl is not None:
        revenue = latest_pl.get("sales")
        net_profit = latest_pl.get("net_profit")
    else:
        revenue = None
        net_profit = None

    if previous_pl is not None:
        previous_revenue = previous_pl.get("sales")
        previous_net_profit = previous_pl.get("net_profit")
    else:
        previous_revenue = None
        previous_net_profit = None

    if latest_ratio is not None:
        roe = latest_ratio.get(
            "return_on_equity_pct"
        )
    else:
        roe = company.get(
            "roe_percentage"
        )

    if previous_ratio is not None:
        previous_roe = previous_ratio.get(
            "return_on_equity_pct"
        )
    else:
        previous_roe = None

    roce = company.get(
        "roce_percentage"
    )

    book_value = company.get(
        "book_value"
    )

    face_value = company.get(
        "face_value"
    )

    return {
        "company_id": company_id,
        "company_name": safe_value(
            company.get("company_name"),
            company_id,
        ),
        "sector": sector,

        "revenue": revenue,
        "revenue_trend": trend_arrow(
            revenue,
            previous_revenue,
        ),

        "net_profit": net_profit,
        "net_profit_trend": trend_arrow(
            net_profit,
            previous_net_profit,
        ),

        "roe": roe,
        "roe_trend": trend_arrow(
            roe,
            previous_roe,
        ),

        # The companies table stores current ROCE only.
        # Therefore no historical ROCE direction is inferred.
        "roce": roce,
        "roce_trend": "→",

        # The companies table stores current book value only.
        # Therefore no historical book-value direction is inferred.
        "book_value": book_value,
        "book_value_trend": "→",

        # Face value is a static company-level field in the database.
        "face_value": face_value,
        "face_value_trend": "→",
    }


# ============================================================================
# COMPANY HEADER
# ============================================================================

def make_company_header(
    summary,
    styles,
):
    """Create company header."""

    company_name = summary["company_name"]
    company_id = summary["company_id"]
    sector = summary["sector"]

    header = Table(
        [
            [
                Paragraph(
                    str(company_name),
                    styles["title"],
                )
            ],
            [
                Paragraph(
                    (
                        f"{company_id} | "
                        f"{sector} | "
                        "N100 Financial Intelligence Platform"
                    ),
                    styles["subtitle"],
                )
            ],
        ],
        colWidths=[182 * mm],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, 0),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, 0),
                    1,
                ),
                (
                    "TOPPADDING",
                    (0, 1),
                    (-1, 1),
                    1,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (-1, 1),
                    7,
                ),
            ]
        )
    )

    return header


# ============================================================================
# KPI TABLE
# ============================================================================

def make_kpi_table(
    summary,
    styles,
):
    """Create six KPI cards with trend arrows."""

    kpis = [
        (
            "Revenue",
            safe_number(summary["revenue"]),
            summary["revenue_trend"],
        ),
        (
            "Net Profit",
            safe_number(summary["net_profit"]),
            summary["net_profit_trend"],
        ),
        (
            "ROE",
            safe_percentage(summary["roe"]),
            summary["roe_trend"],
        ),
        (
            "ROCE",
            safe_percentage(summary["roce"]),
            summary["roce_trend"],
        ),
        (
            "Book Value",
            safe_number(summary["book_value"]),
            summary["book_value_trend"],
        ),
        (
            "Face Value",
            safe_number(summary["face_value"]),
            summary["face_value_trend"],
        ),
    ]

    tiles = []

    for label, value, arrow in kpis:

        arrow_color = (
            GREEN
            if arrow == "↑"
            else RED
            if arrow == "↓"
            else GREY_TEXT
        )

        trend_style = ParagraphStyle(
            f"Trend_{label}",
            parent=styles["trend"],
            textColor=arrow_color,
        )

        tile = Table(
            [
                [
                    Paragraph(
                        label,
                        styles["kpi_label"],
                    )
                ],
                [
                    Paragraph(
                        value,
                        styles["kpi_value"],
                    )
                ],
                [
                    Paragraph(
                        arrow,
                        trend_style,
                    )
                ],
            ],
            colWidths=[54 * mm],
            rowHeights=[
                7 * mm,
                11 * mm,
                7 * mm,
            ],
        )

        tile.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        VERY_LIGHT_BLUE,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        BORDER,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                ]
            )
        )

        tiles.append(tile)

    table = Table(
        [
            tiles[0:3],
            tiles[3:6],
        ],
        colWidths=[
            58 * mm,
            58 * mm,
            58 * mm,
        ],
        hAlign="CENTER",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    return table


# ============================================================================
# TREND LEGEND
# ============================================================================

def make_trend_legend(styles):
    """Create the trend-arrow legend."""

    data = [
        [
            Paragraph(
                "3-Year Trend",
                styles["kpi_label"],
            ),
            Paragraph(
                "↑ Improved",
                styles["small"],
            ),
            Paragraph(
                "↓ Declined",
                styles["small"],
            ),
            Paragraph(
                "→ Flat (within 2%)",
                styles["small"],
            ),
        ]
    ]

    table = Table(
        data,
        colWidths=[
            35 * mm,
            40 * mm,
            40 * mm,
            55 * mm,
        ],
        hAlign="CENTER",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    VERY_LIGHT_BLUE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER,
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
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


# ============================================================================
# COMPANY PAGE
# ============================================================================

def build_company_page(
    summary,
    styles,
):
    """Build one company page."""

    story = []

    story.append(
        make_company_header(
            summary,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            "Top 6 Financial KPIs",
            styles["section"],
        )
    )

    story.append(
        make_kpi_table(
            summary,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    story.append(
        make_trend_legend(
            styles
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        Paragraph(
            "Portfolio Summary Notes",
            styles["section"],
        )
    )

    notes = [
        (
            "Company",
            summary["company_id"],
        ),
        (
            "Sector",
            summary["sector"],
        ),
        (
            "Trend basis",
            "Latest available year versus the latest "
            "available year at least two years earlier",
        ),
        (
            "Flat threshold",
            "Within ±2%",
        ),
        (
            "Currency",
            "₹ crore where applicable",
        ),
    ]

    note_table = Table(
        [
            [
                Paragraph(
                    label,
                    styles["body"],
                ),
                Paragraph(
                    str(value),
                    styles["body"],
                ),
            ]
            for label, value in notes
        ],
        colWidths=[
            50 * mm,
            125 * mm,
        ],
        hAlign="LEFT",
    )

    note_table.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    VERY_LIGHT_BLUE,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
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
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        note_table
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "ROCE, Book Value, and Face Value are stored as "
                "current company-level fields in the database, so "
                "their trend indicator is shown as flat rather than "
                "inferring historical movement."
            ),
            styles["small"],
        )
    )

    return story


# ============================================================================
# PAGE FOOTER
# ============================================================================

def add_page_number(
    canvas,
    document,
):
    """Add portfolio footer and page number."""

    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        6.5,
    )

    canvas.setFillColor(
        GREY_TEXT
    )

    canvas.drawCentredString(
        A4[0] / 2,
        7 * mm,
        (
            "N100 Financial Intelligence Platform"
            f" | Portfolio Summary | Page {document.page}"
        ),
    )

    canvas.restoreState()


# ============================================================================
# VALIDATION
# ============================================================================

def validate_company_universe(
    companies,
):
    """Validate the official 92-company universe."""

    count = companies[
        "company_id"
    ].nunique()

    if count != EXPECTED_COMPANIES:
        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} companies "
            f"but found {count}."
        )


def validate_company_ids(
    summaries,
):
    """Validate that all companies produced a summary."""

    actual_ids = {
        summary["company_id"]
        for summary in summaries
    }

    if len(actual_ids) != EXPECTED_COMPANIES:
        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} company summaries "
            f"but prepared {len(actual_ids)}."
        )


# ============================================================================
# PDF GENERATION
# ============================================================================

def generate_portfolio_summary():
    """Generate the complete Day 35 portfolio summary PDF."""

    print("=" * 72)
    print("SPRINT 5 — DAY 35 PORTFOLIO SUMMARY PDF")
    print("=" * 72)

    print("\nLoading database...")

    (
        companies,
        profit_loss,
        ratios,
        sectors,
    ) = load_portfolio_data()

    print(
        f"Official companies : "
        f"{companies['company_id'].nunique()}"
    )

    print(
        f"Sector records     : "
        f"{len(sectors)}"
    )

    validate_company_universe(
        companies
    )

    # ------------------------------------------------------------------
    # Prepare output directory
    # ------------------------------------------------------------------

    PORTFOLIO_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------------
    # Remove previous Day 35 output
    # ------------------------------------------------------------------

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

        print(
            "\nPrevious portfolio summary removed."
        )

    # ------------------------------------------------------------------
    # Prepare company summaries
    # ------------------------------------------------------------------

    print(
        "\nPreparing company summaries..."
    )

    summaries = []

    for _, company in companies.iterrows():

        summary = prepare_company_summary(
            company=company,
            profit_loss=profit_loss,
            ratios=ratios,
            sectors=sectors,
        )

        summaries.append(
            summary
        )

    # ------------------------------------------------------------------
    # Alphabetical ticker ordering
    # ------------------------------------------------------------------

    summaries = sorted(
        summaries,
        key=lambda item: str(
            item["company_id"]
        ).upper(),
    )

    validate_company_ids(
        summaries
    )

    print(
        f"Company summaries prepared : "
        f"{len(summaries)}"
    )

    # ------------------------------------------------------------------
    # Build PDF
    # ------------------------------------------------------------------

    styles = create_styles()

    document = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        title="N100 Portfolio Summary",
        author="N100 Financial Intelligence Platform",
    )

    story = []

    for index, summary in enumerate(
        summaries
    ):

        print(
            f"[{index + 1}/{len(summaries)}] "
            f"{summary['company_id']}"
        )

        story.extend(
            build_company_page(
                summary,
                styles,
            )
        )

        if index < len(summaries) - 1:
            story.append(
                PageBreak()
            )

    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    # ------------------------------------------------------------------
    # Validate output
    # ------------------------------------------------------------------

    if not OUTPUT_FILE.exists():
        raise FileNotFoundError(
            "Portfolio summary PDF was not created."
        )

    file_size = OUTPUT_FILE.stat().st_size

    if file_size <= 0:
        raise ValueError(
            "Portfolio summary PDF was created but is empty."
        )

    print("\n" + "=" * 72)
    print("DAY 35 PORTFOLIO SUMMARY")
    print("=" * 72)

    print(
        f"Companies included : "
        f"{len(summaries)}"
    )

    print(
        f"Expected pages     : "
        f"{EXPECTED_COMPANIES}"
    )

    print(
        f"Output file        : "
        f"{OUTPUT_FILE}"
    )

    print(
        f"File size          : "
        f"{file_size:,} bytes"
    )

    print(
        "\nSTATUS: PASS"
    )

    print(
        "Portfolio summary PDF generated "
        "with all 92 companies in alphabetical ticker order."
    )

    print("=" * 72)

    return {
        "companies": len(summaries),
        "expected_pages": EXPECTED_COMPANIES,
        "output_file": str(OUTPUT_FILE),
        "status": "PASS",
    }


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    generate_portfolio_summary()