"""
Sprint 5 — Day 33 PDF Tearsheet Generator

Generates a 2-page financial intelligence tearsheet.

Page 1
------
1. Navy company header
2. Six KPI tiles in 2 rows × 3 columns
3. Ten-year Revenue and Net Profit charts
4. ROE and ROCE dual-axis line chart

Page 2
------
1. Balance Sheet composition stacked bar
2. Latest-year Cash Flow waterfall
3. Pros and Cons
4. Capital Allocation badge

Test mode:
    set TEARSHEET_TEST=1

Test companies:
    TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL
"""

from pathlib import Path
import os
import sqlite3
import tempfile

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path("data/nifty100.db")

CASHFLOW_INTELLIGENCE_FILE = Path(
    "outputs/cashflow_intelligence.xlsx"
)

OUTPUT_DIR = Path(
    "reports/tearsheets"
)

EXPECTED_COMPANIES = 92

TEST_COMPANIES = [
    "TCS",
    "HDFCBANK",
    "RELIANCE",
    "SUNPHARMA",
    "TATASTEEL",
]

NAVY = colors.HexColor("#17365D")
LIGHT_BLUE = colors.HexColor("#D9EAF7")
BORDER = colors.HexColor("#C7D1DB")
DARK_TEXT = colors.HexColor("#222222")
GREY_TEXT = colors.HexColor("#666666")
GREEN = colors.HexColor("#2E7D32")
LIGHT_GREEN = colors.HexColor("#E8F5E9")
RED = colors.HexColor("#C62828")
LIGHT_RED = colors.HexColor("#FFEBEE")
WHITE = colors.white


# ============================================================================
# GENERAL HELPERS
# ============================================================================

def scalar_value(value, default=None):
    """Convert a pandas scalar/Series/DataFrame value to one scalar."""
    if isinstance(value, pd.DataFrame):
        if value.empty:
            return default
        value = value.iloc[0, 0]
    elif isinstance(value, pd.Series):
        if value.empty:
            return default
        value = value.iloc[0]
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    return value


def safe_value(value, default="N/A"):
    """Return a readable value for missing data."""

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


def number(value, decimals=2):
    """Format a numeric value."""

    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"

        return f"{float(value):,.{decimals}f}"

    except (TypeError, ValueError):
        return "N/A"


def percentage(value, decimals=2):
    """Format a percentage."""

    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"

        return f"{float(value):.{decimals}f}%"

    except (TypeError, ValueError):
        return "N/A"


def clean_text(value):
    """Convert database text into clean display text."""

    value = safe_value(value, "")

    if not value:
        return ""

    return (
        str(value)
        .replace("\\n", " ")
        .replace("\n", " ")
        .strip()
    )


# ============================================================================
# DATABASE LOADING
# ============================================================================

def load_database():
    """
    Load all datasets required by the Day 33 specification.

    Important:
    Historical cash-flow data comes from the SQLite cashflow table.
    The cashflow_intelligence Excel file does NOT contain year data.
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
                net_profit
            FROM profitandloss
            """,
            connection,
        )

        balance_sheet = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                equity_capital,
                borrowings,
                other_liabilities,
                total_liabilities,
                total_assets
            FROM balancesheet
            """,
            connection,
        )

        cashflow = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
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
        cashflow,
        ratios,
        pros_cons,
    )


def load_cashflow_intelligence():
    """
    Load the existing Day 31/32 cash-flow intelligence output.

    This dataset is NOT treated as historical data because it has
    one row per company and intentionally has no year column.
    """

    if not CASHFLOW_INTELLIGENCE_FILE.exists():
        raise FileNotFoundError(
            "Missing cash-flow intelligence file: "
            f"{CASHFLOW_INTELLIGENCE_FILE}"
        )

    data = pd.read_excel(
        CASHFLOW_INTELLIGENCE_FILE
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
            "Cash-flow intelligence file is missing: "
            + ", ".join(missing)
        )

    return data


# ============================================================================
# DATA FILTERING
# ============================================================================

def company_rows(df, company_id):
    """Return rows belonging to one company using a scalar ID."""
    if df.empty:
        return df.copy()
    company_id = scalar_value(company_id)
    if company_id is None:
        return df.iloc[0:0].copy()
    return df.loc[df["company_id"].eq(company_id)].copy()

def prepare_year_data(df):
    """Convert year to numeric and remove invalid years."""

    result = df.copy()

    if "year" not in result.columns:
        return result

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce",
    )

    result = result.dropna(
        subset=["year"]
    )

    result["year"] = result["year"].astype(int)

    return result.sort_values("year")


def latest_row(df):
    """Return the latest row from a year-based dataset."""

    if df.empty:
        return None

    if "year" not in df.columns:
        return df.iloc[-1]

    prepared = prepare_year_data(df)

    if prepared.empty:
        return None

    return prepared.iloc[-1]


# ============================================================================
# REPORTLAB STYLES
# ============================================================================

def create_styles():
    """Create all PDF text styles."""

    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "TearsheetTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=21,
            textColor=WHITE,
            alignment=TA_LEFT,
        ),

        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#DDE7F0"),
        ),

        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=WHITE,
            backColor=NAVY,
            leftIndent=0,
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
            borderPadding=4,
        ),

        "small": ParagraphStyle(
            "Small",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            textColor=DARK_TEXT,
        ),

        "small_center": ParagraphStyle(
            "SmallCenter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            textColor=DARK_TEXT,
            alignment=TA_CENTER,
        ),

        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=DARK_TEXT,
        ),

        "kpi_label": ParagraphStyle(
            "KPI_Label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8,
            textColor=GREY_TEXT,
            alignment=TA_CENTER,
        ),

        "kpi_value": ParagraphStyle(
            "KPI_Value",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=14,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),

        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            leftIndent=8,
            firstLineIndent=-6,
        ),

        "badge": ParagraphStyle(
            "Badge",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=WHITE,
        ),

        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            alignment=TA_CENTER,
            textColor=GREY_TEXT,
        ),
    }


# ============================================================================
# HEADER
# ============================================================================

def make_header(company_id, company_name, styles):
    """Create the navy company header."""

    header = Table(
        [
            [
                Paragraph(
                    f"{company_name}",
                    styles["title"],
                )
            ],
            [
                Paragraph(
                    f"{company_id} | N100 Financial Intelligence Platform",
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
# KPI TILES
# ============================================================================

def make_kpi_tiles(values, styles):
    """
    Create six KPI tiles in two rows of three.
    """

    tiles = []

    for label, value in values:

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
            ],
            colWidths=[58 * mm],
            rowHeights=[8 * mm, 13 * mm],
        )

        tile.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#F4F8FB"),
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
            60 * mm,
            60 * mm,
            60 * mm,
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
# CHART CREATION
# ============================================================================

def create_revenue_profit_chart(df, company_id, path):
    """Create side-by-side 10-year Revenue and Net Profit bar charts."""

    data = prepare_year_data(df)

    if data.empty or "sales" not in data.columns or "net_profit" not in data.columns:
        fig, ax = plt.subplots(figsize=(10, 3.1))
        ax.text(0.5, 0.5, "Revenue / profit data unavailable", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(f"{company_id} — Revenue & Profit Trend", fontsize=10, fontweight="bold")
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return Path(path).exists()

    data = data.tail(10)

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10, 3.1),
    )

    axes[0].bar(
        data["year"].astype(str),
        data["sales"],
    )

    axes[0].set_title(
        "Revenue — Last 10 Years",
        fontsize=9,
    )

    axes[0].tick_params(
        axis="x",
        rotation=45,
        labelsize=7,
    )

    axes[0].tick_params(
        axis="y",
        labelsize=7,
    )

    axes[0].set_ylabel(
        "Value",
        fontsize=7,
    )

    axes[1].bar(
        data["year"].astype(str),
        data["net_profit"],
    )

    axes[1].set_title(
        "Net Profit — Last 10 Years",
        fontsize=9,
    )

    axes[1].tick_params(
        axis="x",
        rotation=45,
        labelsize=7,
    )

    axes[1].tick_params(
        axis="y",
        labelsize=7,
    )

    axes[1].set_ylabel(
        "Value",
        fontsize=7,
    )

    fig.suptitle(
        f"{company_id} — Revenue & Profit Trend",
        fontsize=10,
        fontweight="bold",
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    return True


def create_roe_roce_chart(ratio_df, company, company_id, path):
    """Create the ROE/ROCE chart with a consistent argument order."""
    company_id = str(scalar_value(company_id, "UNKNOWN"))
    data = prepare_year_data(ratio_df)

    if not data.empty and "return_on_equity_pct" in data.columns:
        data = data.tail(10).copy()
        data["return_on_equity_pct"] = pd.to_numeric(
            data["return_on_equity_pct"], errors="coerce"
        )
        data = data.dropna(subset=["year", "return_on_equity_pct"])

    roce = scalar_value(company.get("roce_percentage"))

    fig, ax1 = plt.subplots(figsize=(10, 2.8))

    if not data.empty:
        years = data["year"].astype(int).tolist()
        roe = data["return_on_equity_pct"].astype(float).tolist()
        ax1.plot(years, roe, marker="o", linewidth=1.8, label="ROE")
        ax1.set_xlabel("Year", fontsize=8)
        ax1.set_ylabel("ROE (%)", fontsize=8)
        ax1.tick_params(axis="both", labelsize=7)

        ax2 = ax1.twinx()
        try:
            roce_float = float(roce)
        except (TypeError, ValueError):
            roce_float = None

        if roce_float is not None:
            ax2.plot(
                years, [roce_float] * len(years),
                linestyle="--", linewidth=1.8, label="ROCE"
            )

        ax2.set_ylabel("ROCE (%)", fontsize=8)
        ax2.tick_params(axis="y", labelsize=7)

        l1, lab1 = ax1.get_legend_handles_labels()
        l2, lab2 = ax2.get_legend_handles_labels()
        if l1 or l2:
            ax1.legend(l1 + l2, lab1 + lab2, loc="best", fontsize=7)
    else:
        labels = []
        values = []
        roe_current = scalar_value(company.get("roe_percentage"))
        for label, value in (("ROE", roe_current), ("ROCE", roce)):
            try:
                if value is not None:
                    labels.append(label)
                    values.append(float(value))
            except (TypeError, ValueError):
                pass
        if values:
            ax1.bar(labels, values)
            ax1.set_ylabel("Percentage (%)", fontsize=8)
        else:
            ax1.text(0.5, 0.5, "ROE / ROCE data unavailable",
                     ha="center", va="center", transform=ax1.transAxes)
            ax1.set_xticks([])
            ax1.set_yticks([])

    ax1.set_title(f"{company_id} — ROE & ROCE", fontsize=9, fontweight="bold")
    ax1.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return Path(path).exists()

def create_balance_chart(df, company_id, path):
    """Create stacked balance-sheet composition chart."""

    data = prepare_year_data(df)

    required = {"equity_capital", "borrowings", "other_liabilities"}

    if data.empty or not required.issubset(data.columns):
        fig, ax = plt.subplots(figsize=(10, 3.0))
        ax.text(0.5, 0.5, "Balance-sheet data unavailable", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(f"{company_id} — Balance Sheet Composition", fontsize=9, fontweight="bold")
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return Path(path).exists()

    data = data.tail(10)

    fig, ax = plt.subplots(
        figsize=(10, 3.0)
    )

    ax.bar(
        data["year"].astype(str),
        data["equity_capital"].fillna(0),
        label="Equity",
    )

    ax.bar(
        data["year"].astype(str),
        data["borrowings"].fillna(0),
        bottom=data["equity_capital"].fillna(0),
        label="Borrowings",
    )

    bottom = (
        data["equity_capital"].fillna(0)
        + data["borrowings"].fillna(0)
    )

    ax.bar(
        data["year"].astype(str),
        data["other_liabilities"].fillna(0),
        bottom=bottom,
        label="Other Liabilities",
    )

    ax.set_title(
        f"{company_id} — Balance Sheet Composition",
        fontsize=9,
        fontweight="bold",
    )

    ax.set_ylabel(
        "Value",
        fontsize=8,
    )

    ax.tick_params(
        axis="x",
        rotation=45,
        labelsize=7,
    )

    ax.tick_params(
        axis="y",
        labelsize=7,
    )

    ax.legend(
        fontsize=7,
        loc="upper left",
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    return True


def create_cashflow_waterfall(df, company_id, path):
    """Create latest-year cash-flow waterfall."""

    data = prepare_year_data(df)

    if data.empty or not {"operating_activity", "investing_activity", "financing_activity", "net_cash_flow"}.issubset(data.columns):
        fig, ax = plt.subplots(figsize=(10, 3.0))
        ax.text(0.5, 0.5, "Cash-flow data unavailable", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(f"{company_id} — Latest-Year Cash Flow", fontsize=9, fontweight="bold")
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return Path(path).exists()

    latest = data.iloc[-1]

    values = [
        float(latest["operating_activity"]),
        float(latest["investing_activity"]),
        float(latest["financing_activity"]),
        float(latest["net_cash_flow"]),
    ]

    labels = [
        "CFO",
        "CFI",
        "CFF",
        "Net Cash Flow",
    ]

    fig, ax = plt.subplots(
        figsize=(10, 3.0)
    )

    cumulative = 0

    for index in range(3):

        value = values[index]

        ax.bar(
            index,
            value,
            bottom=cumulative if value >= 0 else cumulative + value,
        )

        cumulative += value

    ax.bar(
        3,
        values[3],
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    ax.set_xticks(
        range(4)
    )

    ax.set_xticklabels(
        labels,
        fontsize=8,
    )

    ax.set_ylabel(
        "Cash Flow",
        fontsize=8,
    )

    ax.set_title(
        f"{company_id} — Latest-Year Cash Flow",
        fontsize=9,
        fontweight="bold",
    )

    ax.tick_params(
        axis="y",
        labelsize=7,
    )

    ax.text(
        3,
        values[3],
        number(values[3]),
        ha="center",
        va="bottom" if values[3] >= 0 else "top",
        fontsize=7,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    return True


# ============================================================================
# PROS / CONS
# ============================================================================

def split_points(text):
    """
    Convert generated pros/cons text into readable bullet points.
    """

    text = clean_text(text)

    if not text:
        return ["Not available"]

    separators = [
        "•",
        "\n",
        ";",
    ]

    for separator in separators:

        if separator in text:

            points = [
                item.strip(" -•")
                for item in text.split(separator)
                if item.strip(" -•")
            ]

            if points:
                return points

    return [text]


def make_bullet_section(
    title,
    points,
    style,
    background,
):
    """Create wrapped bullet-point section."""

    rows = []

    for point in points:

        rows.append(
            [
                Paragraph(
                    f"• {point}",
                    style,
                )
            ]
        )

    table = Table(
        rows,
        colWidths=[88 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    background,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
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

    heading = Paragraph(
        title,
        ParagraphStyle(
            f"{title}_Heading",
            parent=style,
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=GREEN if "Pros" in title else RED,
        ),
    )

    return [
        heading,
        table,
    ]


# ============================================================================
# CAPITAL ALLOCATION
# ============================================================================

def make_capital_badge(label, styles):
    """Create capital allocation badge."""

    label = safe_value(
        label,
        "Unknown",
    )

    badge = Table(
        [
            [
                Paragraph(
                    "CAPITAL ALLOCATION",
                    styles["small_center"],
                )
            ],
            [
                Paragraph(
                    str(label),
                    styles["badge"],
                )
            ],
        ],
        colWidths=[70 * mm],
        rowHeights=[8 * mm, 15 * mm],
    )

    badge.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    LIGHT_BLUE,
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, 1),
                    NAVY,
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
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    NAVY,
                ),
            ]
        )
    )

    return badge


# ============================================================================
# PDF FOOTER
# ============================================================================

def add_page_number(canvas, document):
    """Add footer and page number."""

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
        f"N100 Financial Intelligence Platform | Page {document.page}",
    )

    canvas.restoreState()


# ============================================================================
# SINGLE COMPANY TEARSHEET
# ============================================================================

def build_tearsheet(
    company,
    profit_loss,
    balance_sheet,
    cashflow,
    ratios,
    pros_cons,
    intelligence,
    styles,
    output_path,
    chart_directory,
):
    """Build the complete two-page company tearsheet."""

    company_id = str(scalar_value(company.get("company_id"))).strip()

    company_name = clean_text(
        company.get("company_name")
    )

    if not company_name:
        company_name = company_id

    # ------------------------------------------------------------------
    # Company datasets
    # ------------------------------------------------------------------

    pl = prepare_year_data(
        company_rows(
            profit_loss,
            company_id,
        )
    )

    bs = prepare_year_data(
        company_rows(
            balance_sheet,
            company_id,
        )
    )

    cf = prepare_year_data(
        company_rows(
            cashflow,
            company_id,
        )
    )

    ratio = prepare_year_data(
        company_rows(
            ratios,
            company_id,
        )
    )

    intelligence_row = intelligence.loc[
        intelligence["company_id"].eq(company_id)
    ].copy()

    if intelligence_row.empty:
        intel = None
    else:
        intel = intelligence_row.iloc[0]

    pros_cons_row = pros_cons.loc[
        pros_cons["company_id"].eq(company_id)
    ].copy()

    if pros_cons_row.empty:
        pros = ["Not available"]
        cons = ["Not available"]
    else:
        row = pros_cons_row.iloc[0]

        pros = split_points(
            row.get("pros")
        )

        cons = split_points(
            row.get("cons")
        )

    latest_pl = latest_row(pl)
    latest_cf = latest_row(cf)

    # ------------------------------------------------------------------
    # Temporary chart files
    # ------------------------------------------------------------------

    # Use a unique temporary directory for chart images so stale or
    # locked files in reports/tearsheets/_charts cannot break generation.
    temp_chart_dir = Path(
        tempfile.mkdtemp(prefix=f"tearsheet_{company_id}_")
    )

    revenue_profit_path = temp_chart_dir / f"{company_id}_revenue_profit.png"
    roe_roce_path = temp_chart_dir / f"{company_id}_roe_roce.png"
    balance_path = temp_chart_dir / f"{company_id}_balance.png"
    waterfall_path = temp_chart_dir / f"{company_id}_cashflow.png"

    # Create every chart before ReportLab tries to embed the PNG files.
    if not create_revenue_profit_chart(pl, company_id, revenue_profit_path):
        raise ValueError(f"Revenue/profit chart data unavailable for {company_id}.")

    if not create_roe_roce_chart(ratio, company, company_id, roe_roce_path):
        raise ValueError(f"ROE/ROCE chart could not be created for {company_id}.")

    if not create_balance_chart(bs, company_id, balance_path):
        raise ValueError(f"Balance-sheet chart data unavailable for {company_id}.")

    if not create_cashflow_waterfall(cf, company_id, waterfall_path):
        raise ValueError(f"Cash-flow chart data unavailable for {company_id}.")

    # ------------------------------------------------------------------
    # Document
    # ------------------------------------------------------------------

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
    )

    story = []

    # ==================================================================
    # PAGE 1
    # ==================================================================

    story.append(
        make_header(
            company_id,
            company_name,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    # ------------------------------------------------------------------
    # Six KPIs
    # ------------------------------------------------------------------

    if latest_pl is not None:

        latest_sales = latest_pl.get(
            "sales"
        )

        latest_profit = latest_pl.get(
            "net_profit"
        )

    else:

        latest_sales = None
        latest_profit = None

    latest_roe = (
        scalar_value(ratio.iloc[-1]["return_on_equity_pct"])
        if not ratio.empty
        else scalar_value(company.get("roe_percentage"))
    )

    kpis = [
        (
            "Revenue",
            number(latest_sales),
        ),
        (
            "Net Profit",
            number(latest_profit),
        ),
        (
            "ROE",
            percentage(latest_roe),
        ),
        (
            "ROCE",
            percentage(
                company.get("roce_percentage")
            ),
        ),
        (
            "Book Value",
            number(
                company.get("book_value")
            ),
        ),
        (
            "Face Value",
            number(
                company.get("face_value")
            ),
        ),
    ]

    story.append(
        make_kpi_tiles(
            kpis,
            styles,
        )
    )

    story.append(
        Paragraph(
            "10-Year Revenue & Net Profit",
            styles["section"],
        )
    )

    story.append(
        Image(
            str(revenue_profit_path),
            width=180 * mm,
            height=58 * mm,
        )
    )

    story.append(
        Paragraph(
            "ROE & ROCE Trend",
            styles["section"],
        )
    )

    story.append(
        Image(
            str(roe_roce_path),
            width=180 * mm,
            height=51 * mm,
        )
    )

    # ==================================================================
    # PAGE 2
    # ==================================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Balance Sheet Composition",
            styles["section"],
        )
    )

    story.append(
        Image(
            str(balance_path),
            width=180 * mm,
            height=54 * mm,
        )
    )

    story.append(
        Paragraph(
            "Latest-Year Cash Flow",
            styles["section"],
        )
    )

    story.append(
        Image(
            str(waterfall_path),
            width=180 * mm,
            height=50 * mm,
        )
    )

    # ------------------------------------------------------------------
    # Pros and Cons
    # ------------------------------------------------------------------

    story.append(
        Paragraph(
            "Business Signals",
            styles["section"],
        )
    )

    pros_table = make_bullet_section(
        "Pros",
        pros,
        styles["bullet"],
        LIGHT_GREEN,
    )

    cons_table = make_bullet_section(
        "Cons",
        cons,
        styles["bullet"],
        LIGHT_RED,
    )

    signals = Table(
        [
            [
                pros_table[1],
                cons_table[1],
            ]
        ],
        colWidths=[
            89 * mm,
            89 * mm,
        ],
    )

    signals.setStyle(
        TableStyle(
            [
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
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    headings = Table(
        [
            [
                pros_table[0],
                cons_table[0],
            ]
        ],
        colWidths=[
            89 * mm,
            89 * mm,
        ],
    )

    headings.setStyle(
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
            ]
        )
    )

    story.append(
        headings
    )

    story.append(
        signals
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # ------------------------------------------------------------------
    # Capital allocation
    # ------------------------------------------------------------------

    capital_label = (
        intel["capital_allocation_label"]
        if intel is not None
        else "Unknown"
    )

    capital_badge = make_capital_badge(
        capital_label,
        styles,
    )

    capital_table = Table(
        [
            [
                capital_badge,
                Paragraph(
                    (
                        f"<b>Sector:</b> "
                        f"{safe_value(intel.get('sector'))}<br/>"
                        f"<b>CFO Quality:</b> "
                        f"{safe_value(intel.get('cfo_quality_label'))}<br/>"
                        f"<b>Capex:</b> "
                        f"{percentage(intel.get('capex_intensity_pct'))}<br/>"
                        f"<b>Distress Flag:</b> "
                        f"{safe_value(intel.get('distress_flag'))}"
                    )
                    if intel is not None
                    else "Cash-flow intelligence not available.",
                    styles["small"],
                ),
            ]
        ],
        colWidths=[
            75 * mm,
            103 * mm,
        ],
    )

    capital_table.setStyle(
        TableStyle(
            [
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
            ]
        )
    )

    story.append(
        capital_table
    )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    story.append(
        Paragraph(
            "Analytical output for research and screening purposes.",
            styles["footer"],
        )
    )

    # ------------------------------------------------------------------
    # Build PDF
    # ------------------------------------------------------------------

    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    # Remove temporary chart files after ReportLab has finished reading them.
    for chart_path in (
        revenue_profit_path,
        roe_roce_path,
        balance_path,
        waterfall_path,
    ):
        try:
            chart_path.unlink(missing_ok=True)
        except TypeError:
            if chart_path.exists():
                chart_path.unlink()
        except OSError:
            pass

    try:
        temp_chart_dir.rmdir()
    except OSError:
        pass


# ============================================================================
# VALIDATION
# ============================================================================

def validate_data(
    companies,
    profit_loss,
    balance_sheet,
    cashflow,
    ratios,
):
    """Validate the minimum required dataset structure."""

    if companies["company_id"].nunique() != EXPECTED_COMPANIES:
        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} companies but found "
            f"{companies['company_id'].nunique()}."
        )

    required_columns = {
        "profitandloss": {
            "company_id",
            "year",
            "sales",
            "net_profit",
        },
        "balancesheet": {
            "company_id",
            "year",
            "equity_capital",
            "borrowings",
            "other_liabilities",
        },
        "cashflow": {
            "company_id",
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        },
        "financial_ratios": {
            "company_id",
            "year",
            "return_on_equity_pct",
        },
    }

    datasets = {
        "profitandloss": profit_loss,
        "balancesheet": balance_sheet,
        "cashflow": cashflow,
        "financial_ratios": ratios,
    }

    for name, required in required_columns.items():

        missing = required - set(
            datasets[name].columns
        )

        if missing:
            raise ValueError(
                f"{name} is missing columns: "
                + ", ".join(sorted(missing))
            )


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate():
    """Generate Day 33 tearsheets."""

    print("=" * 72)
    print("SPRINT 5 — DAY 33 PDF TEARSHEET GENERATOR")
    print("=" * 72)

    print("\nLoading database...")

    (
        companies,
        profit_loss,
        balance_sheet,
        cashflow,
        ratios,
        pros_cons,
    ) = load_database()

    print(
        f"Official companies : "
        f"{companies['company_id'].nunique()}"
    )

    print(
        "\nLoading cash-flow intelligence..."
    )

    intelligence = load_cashflow_intelligence()

    print(
        f"Cash-flow records  : "
        f"{len(intelligence)}"
    )

    validate_data(
        companies,
        profit_loss,
        balance_sheet,
        cashflow,
        ratios,
    )

    test_mode = (
        os.environ.get(
            "TEARSHEET_TEST",
            "",
        ).strip()
        == "1"
    )

    if test_mode:

        selected = companies[
            companies["company_id"].isin(
                TEST_COMPANIES
            )
        ].copy()

        selected["sort_order"] = (
            selected["company_id"]
            .map(
                {
                    ticker: index
                    for index, ticker
                    in enumerate(TEST_COMPANIES)
                }
            )
        )

        selected = selected.sort_values(
            "sort_order"
        )

        print("\nTEST MODE:")
        print(
            ", ".join(
                selected["company_id"].tolist()
            )
        )

    else:

        selected = companies.copy()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    chart_directory = (
        OUTPUT_DIR / "_charts"
    )

    styles = create_styles()

    generated = 0
    failed = []

    company_records = selected.to_dict(orient="records")

    for company in company_records:

        company_id = company["company_id"]

        output_path = (
            OUTPUT_DIR
            / f"{company_id}_tearsheet.pdf"
        )

        try:

            build_tearsheet(
                company=company,
                profit_loss=profit_loss,
                balance_sheet=balance_sheet,
                cashflow=cashflow,
                ratios=ratios,
                pros_cons=pros_cons,
                intelligence=intelligence,
                styles=styles,
                output_path=output_path,
                chart_directory=chart_directory,
            )

            generated += 1

            print(
                f"[{generated}/{len(selected)}] "
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

    print("\n" + "=" * 72)
    print(
        f"PDFs generated     : {generated}"
    )
    print(
        f"Failed             : {len(failed)}"
    )

    if failed:

        print(
            "STATUS: REVIEW"
        )

        print(
            "\nFailures:"
        )

        for company_id, error in failed:
            print(
                f"  {company_id}: {error}"
            )

    else:

        print(
            "STATUS: PASS"
        )

    print("=" * 72)

    return generated, failed


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    generate()