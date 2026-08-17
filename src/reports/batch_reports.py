"""
Sprint 5 — Day 34 Batch Report Generation

Generates:
    1. Company tearsheets for all eligible companies
    2. skipped_tearsheets.csv for companies with < 3 years of P&L data
    3. Sector reports for every broad sector present in the database

Output structure:

    reports/
    ├── tearsheets/
    │   ├── ABB_tearsheet.pdf
    │   ├── RELIANCE_tearsheet.pdf
    │   └── ...
    │
    ├── sector/
    │   ├── Communication Services_report.pdf
    │   ├── Financials_report.pdf
    │   └── ...
    │
    └── skipped_tearsheets.csv

The existing Day 33 tearsheet generator is reused.
"""

from pathlib import Path
import sqlite3

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
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
)


# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path("data/nifty100.db")

# All Day 34 generated reports live directly under reports/
REPORTS_DIR = Path("reports")

TEARSHEET_DIR = REPORTS_DIR / "tearsheets"
SECTOR_DIR = REPORTS_DIR / "sector"

# Temporary chart files used by the Day 33 tearsheet generator
CHART_DIR = TEARSHEET_DIR / "_charts"

SKIPPED_FILE = REPORTS_DIR / "skipped_tearsheets.csv"

MIN_YEARS_REQUIRED = 3
EXPECTED_COMPANIES = 92


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

BEST_BG = colors.HexColor("#E8F5E9")
WORST_BG = colors.HexColor("#FFEBEE")


# ============================================================================
# DATABASE LOADING
# ============================================================================

def load_day34_data():
    """Load datasets required for Day 34 reports."""

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
                net_profit_margin_pct,
                operating_profit_margin_pct,
                return_on_equity_pct,
                debt_to_equity,
                interest_coverage,
                free_cash_flow_cr,
                cash_from_operations_cr
            FROM financial_ratios
            """,
            connection,
        )

        growth = pd.read_sql_query(
            """
            SELECT
                company_id,
                revenue_cagr_3y,
                revenue_cagr_5y,
                revenue_cagr_10y,
                pat_cagr_3y,
                pat_cagr_5y,
                eps_cagr_5y
            FROM company_growth_metrics
            """,
            connection,
        )

        market_cap = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                market_cap_crore,
                enterprise_value_crore,
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield_pct
            FROM market_cap
            """,
            connection,
        )

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector,
                sub_sector,
                index_weight_pct,
                market_cap_category
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
        growth,
        market_cap,
        sectors,
    )


# ============================================================================
# GENERAL HELPERS
# ============================================================================

def numeric_value(value):
    """Convert value to numeric or NaN."""

    return pd.to_numeric(
        value,
        errors="coerce",
    )


def safe_number(value, decimals=2):
    """Return a readable numeric value."""

    try:
        if pd.isna(value):
            return "N/A"

        return f"{float(value):,.{decimals}f}"

    except (TypeError, ValueError):
        return "N/A"


def safe_percentage(value, decimals=2):
    """Return a readable percentage."""

    try:
        if pd.isna(value):
            return "N/A"

        return f"{float(value):.{decimals}f}%"

    except (TypeError, ValueError):
        return "N/A"


def clean_filename(text):
    """Convert text into a filesystem-safe filename."""

    text = str(text).strip()

    for character in [
        "/",
        "\\",
        ":",
        "*",
        "?",
        '"',
        "<",
        ">",
        "|",
    ]:
        text = text.replace(character, "_")

    return text


def latest_by_year(df):
    """Return latest row according to numeric year."""

    if df.empty:
        return None

    if "year" not in df.columns:
        return df.iloc[-1]

    result = df.copy()

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce",
    )

    result = result.dropna(
        subset=["year"]
    )

    if result.empty:
        return None

    result["year"] = result["year"].astype(int)

    return result.sort_values(
        "year"
    ).iloc[-1]


def median_value(series):
    """Return formatted median."""

    values = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if values.empty:
        return "N/A"

    return f"{values.median():,.2f}"


def median_percentage(series):
    """Return formatted percentage median."""

    values = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if values.empty:
        return "N/A"

    return f"{values.median():.2f}%"


# ============================================================================
# OUTPUT CLEANUP
# ============================================================================

def clean_previous_batch_outputs():
    """
    Remove previous Day 34-generated company and sector PDFs.

    This prevents stale files from being counted as newly generated
    reports.
    """

    TEARSHEET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    SECTOR_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    removed_company = 0
    removed_sector = 0

    for path in TEARSHEET_DIR.glob("*_tearsheet.pdf"):
        path.unlink()
        removed_company += 1

    for path in SECTOR_DIR.glob("*_report.pdf"):
        path.unlink()
        removed_sector += 1

    print(
        f"Previous company PDFs removed : {removed_company}"
    )

    print(
        f"Previous sector PDFs removed  : {removed_sector}"
    )


# ============================================================================
# COMPANY ELIGIBILITY
# ============================================================================

def find_skipped_companies(
    companies,
    profit_loss,
):
    """
    Find companies having fewer than three distinct P&L years.
    """

    pl = profit_loss.copy()

    pl["year"] = pd.to_numeric(
        pl["year"],
        errors="coerce",
    )

    year_counts = (
        pl
        .dropna(subset=["year"])
        .groupby("company_id")["year"]
        .nunique()
    )

    skipped = []

    for _, company in companies.iterrows():

        company_id = company["company_id"]

        years = int(
            year_counts.get(
                company_id,
                0,
            )
        )

        if years < MIN_YEARS_REQUIRED:

            skipped.append(
                {
                    "company_id": company_id,
                    "company_name": company["company_name"],
                    "years_available": years,
                    "minimum_required": MIN_YEARS_REQUIRED,
                    "reason": (
                        "Fewer than 3 years of "
                        "profit and loss data"
                    ),
                }
            )

    return pd.DataFrame(
        skipped,
        columns=[
            "company_id",
            "company_name",
            "years_available",
            "minimum_required",
            "reason",
        ],
    )


def save_skipped_companies(skipped):
    """Save skipped company information."""

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    skipped.to_csv(
        SKIPPED_FILE,
        index=False,
    )


# ============================================================================
# COMPANY TEARSHEET BATCH
# ============================================================================

def generate_company_tearsheets(
    companies,
    skipped,
):
    """
    Generate tearsheets for all Day 34 eligible companies
    using the existing Day 33 tearsheet generator.
    """

    from src.reports.tearsheet import (
        load_database,
        create_styles,
        build_tearsheet,
        load_cashflow_intelligence,
    )

    print("\n" + "=" * 72)
    print("COMPANY TEARSHEET BATCH GENERATION")
    print("=" * 72)

    # ------------------------------------------------------------------
    # Load the exact datasets used by Day 33
    #
    # IMPORTANT:
    # load_database() returns:
    # companies,
    # profit_loss,
    # balance_sheet,
    # cashflow,
    # ratios,
    # pros_cons
    # ------------------------------------------------------------------

    (
        db_companies,
        profit_loss,
        balance_sheet,
        cashflow,
        ratios,
        pros_cons,
    ) = load_database()

    intelligence = load_cashflow_intelligence()

    # ------------------------------------------------------------------
    # Validate Day 33 company universe
    # ------------------------------------------------------------------

    db_company_count = db_companies["company_id"].nunique()

    if db_company_count != EXPECTED_COMPANIES:
        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} companies in Day 33 "
            f"tearsheet data but found {db_company_count}."
        )

    # ------------------------------------------------------------------
    # Determine eligible companies
    # ------------------------------------------------------------------

    skipped_ids = set(
        skipped["company_id"].tolist()
    )

    eligible = companies[
        ~companies["company_id"].isin(skipped_ids)
    ].copy()

    # Preserve official company ordering
    eligible = eligible.sort_values(
        "company_id"
    )

    TEARSHEET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Day 33 generates temporary charts for every company.
    CHART_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------------
    # Create Day 33 styles once
    # ------------------------------------------------------------------

    report_styles = create_styles()

    generated = 0
    failed = []

    print(
        f"\nEligible companies : {len(eligible)}"
    )

    print(
        f"Skipped companies  : {len(skipped)}"
    )

    # ------------------------------------------------------------------
    # Generate one PDF per eligible company
    # ------------------------------------------------------------------

    for _, company in eligible.iterrows():

        company_id = company["company_id"]

        output_path = (
            TEARSHEET_DIR
            / f"{company_id}_tearsheet.pdf"
        )

        try:

            # IMPORTANT:
            # These keyword names must exactly match the Day 33
            # build_tearsheet() function signature.
            build_tearsheet(
                company=company,
                profit_loss=profit_loss,
                balance_sheet=balance_sheet,
                cashflow=cashflow,
                ratios=ratios,
                pros_cons=pros_cons,
                intelligence=intelligence,
                styles=report_styles,
                output_path=output_path,
                chart_directory=CHART_DIR,
            )

            if not output_path.exists():
                raise FileNotFoundError(
                    f"Expected tearsheet PDF was not created: "
                    f"{output_path}"
                )

            generated += 1

            print(
                f"[{generated}/{len(eligible)}] "
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

    return generated, failed


# ============================================================================
# SECTOR REPORT STYLES
# ============================================================================

def create_sector_styles():
    """Create ReportLab styles for sector reports."""

    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "SectorTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=WHITE,
            alignment=TA_LEFT,
        ),

        "subtitle": ParagraphStyle(
            "SectorSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#DDE7F0"),
        ),

        "section": ParagraphStyle(
            "SectorSection",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=WHITE,
            backColor=NAVY,
            borderPadding=4,
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
        ),

        "body": ParagraphStyle(
            "SectorBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=DARK_TEXT,
        ),

        "small": ParagraphStyle(
            "SectorSmall",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            textColor=DARK_TEXT,
        ),

        "small_center": ParagraphStyle(
            "SectorSmallCenter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            alignment=TA_CENTER,
            textColor=DARK_TEXT,
        ),

        "footer": ParagraphStyle(
            "SectorFooter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            alignment=TA_CENTER,
            textColor=GREY_TEXT,
        ),
    }


# ============================================================================
# SECTOR METRICS
# ============================================================================

def prepare_company_metrics(
    sector_companies,
    profit_loss,
    ratios,
    growth,
    market_cap,
    companies,
):
    """
    Build one row per company with sector-report metrics.

    Metrics:
        Revenue
        Net Profit
        ROE
        ROCE
        Debt / Equity
        Free Cash Flow
        Revenue CAGR 5Y
        P/E
    """

    rows = []

    for _, sector_company in sector_companies.iterrows():

        company_id = sector_company[
            "company_id"
        ]

        company_match = companies[
            companies["company_id"] == company_id
        ]

        if company_match.empty:
            continue

        company = company_match.iloc[0]

        company_pl = profit_loss[
            profit_loss["company_id"] == company_id
        ].copy()

        company_pl["year"] = pd.to_numeric(
            company_pl["year"],
            errors="coerce",
        )

        company_pl = company_pl.dropna(
            subset=["year"]
        )

        latest_pl = latest_by_year(
            company_pl
        )

        company_ratios = ratios[
            ratios["company_id"] == company_id
        ].copy()

        latest_ratio = latest_by_year(
            company_ratios
        )

        company_growth = growth[
            growth["company_id"] == company_id
        ]

        growth_row = (
            company_growth.iloc[0]
            if not company_growth.empty
            else None
        )

        company_market = market_cap[
            market_cap["company_id"] == company_id
        ].copy()

        latest_market = latest_by_year(
            company_market
        )

        revenue = (
            latest_pl.get("sales")
            if latest_pl is not None
            else None
        )

        net_profit = (
            latest_pl.get("net_profit")
            if latest_pl is not None
            else None
        )

        if latest_ratio is not None:

            roe = latest_ratio.get(
                "return_on_equity_pct"
            )

            debt_equity = latest_ratio.get(
                "debt_to_equity"
            )

            free_cash_flow = latest_ratio.get(
                "free_cash_flow_cr"
            )

        else:

            roe = company.get(
                "roe_percentage"
            )

            debt_equity = None
            free_cash_flow = None

        roce = company.get(
            "roce_percentage"
        )

        revenue_cagr_5y = (
            growth_row.get(
                "revenue_cagr_5y"
            )
            if growth_row is not None
            else None
        )

        pe_ratio = (
            latest_market.get(
                "pe_ratio"
            )
            if latest_market is not None
            else None
        )

        rows.append(
            {
                "company_id": company_id,
                "company_name": company.get(
                    "company_name"
                ),
                "revenue": numeric_value(
                    revenue
                ),
                "net_profit": numeric_value(
                    net_profit
                ),
                "roe": numeric_value(
                    roe
                ),
                "roce": numeric_value(
                    roce
                ),
                "debt_equity": numeric_value(
                    debt_equity
                ),
                "free_cash_flow": numeric_value(
                    free_cash_flow
                ),
                "revenue_cagr_5y": numeric_value(
                    revenue_cagr_5y
                ),
                "pe_ratio": numeric_value(
                    pe_ratio
                ),
            }
        )

    return pd.DataFrame(rows)


# ============================================================================
# SECTOR HEADER
# ============================================================================

def make_sector_header(
    sector_name,
    company_count,
    styles,
):
    """Create sector report header."""

    table = Table(
        [
            [
                Paragraph(
                    sector_name,
                    styles["title"],
                )
            ],
            [
                Paragraph(
                    (
                        "N100 Financial Intelligence Platform"
                        f" | {company_count} companies"
                    ),
                    styles["subtitle"],
                )
            ],
        ],
        colWidths=[260 * mm],
    )

    table.setStyle(
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
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, 0),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 1),
                    (-1, 1),
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (-1, 1),
                    8,
                ),
            ]
        )
    )

    return table


# ============================================================================
# SECTOR SUMMARY
# ============================================================================

def make_sector_summary(
    metrics,
    styles,
):
    """Create median KPI summary table."""

    summary_data = [
        [
            "Median KPI",
            "Sector Median",
        ],
        [
            "Revenue",
            median_value(
                metrics["revenue"]
            ),
        ],
        [
            "Net Profit",
            median_value(
                metrics["net_profit"]
            ),
        ],
        [
            "ROE",
            median_percentage(
                metrics["roe"]
            ),
        ],
        [
            "ROCE",
            median_percentage(
                metrics["roce"]
            ),
        ],
        [
            "Debt / Equity",
            median_value(
                metrics["debt_equity"]
            ),
        ],
        [
            "Free Cash Flow",
            median_value(
                metrics["free_cash_flow"]
            ),
        ],
        [
            "Revenue CAGR 5Y",
            median_percentage(
                metrics["revenue_cagr_5y"]
            ),
        ],
        [
            "P/E",
            median_value(
                metrics["pe_ratio"]
            ),
        ],
    ]

    table = Table(
        summary_data,
        colWidths=[
            90 * mm,
            70 * mm,
        ],
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    WHITE,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    VERY_LIGHT_BLUE,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER,
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
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

    return table


# ============================================================================
# COMPANY TABLE
# ============================================================================

def make_company_table(
    metrics,
    styles,
):
    """
    Create company-level sector table.

    Best/worst are highlighted using latest available ROE,
    which is the primary profitability metric used for the
    sector ranking.
    """

    headers = [
        "Company",
        "Revenue",
        "Net Profit",
        "ROE",
        "ROCE",
        "D/E",
        "FCF",
        "Rev CAGR 5Y",
        "P/E",
    ]

    data = [headers]

    valid_roe = metrics[
        metrics["roe"].notna()
    ]

    best_company = None
    worst_company = None

    if not valid_roe.empty:

        best_company = valid_roe.loc[
            valid_roe["roe"].idxmax(),
            "company_id",
        ]

        worst_company = valid_roe.loc[
            valid_roe["roe"].idxmin(),
            "company_id",
        ]

    row_company_ids = []

    for _, row in metrics.iterrows():

        row_company_ids.append(
            row["company_id"]
        )

        data.append(
            [
                Paragraph(
                    str(row["company_id"]),
                    styles["small"],
                ),
                safe_number(
                    row["revenue"]
                ),
                safe_number(
                    row["net_profit"]
                ),
                safe_percentage(
                    row["roe"]
                ),
                safe_percentage(
                    row["roce"]
                ),
                safe_number(
                    row["debt_equity"]
                ),
                safe_number(
                    row["free_cash_flow"]
                ),
                safe_percentage(
                    row["revenue_cagr_5y"]
                ),
                safe_number(
                    row["pe_ratio"]
                ),
            ]
        )

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            27 * mm,
            25 * mm,
            25 * mm,
            20 * mm,
            20 * mm,
            18 * mm,
            25 * mm,
            25 * mm,
            20 * mm,
        ],
        hAlign="CENTER",
    )

    style_commands = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            NAVY,
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            WHITE,
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
            6.2,
        ),
        (
            "ALIGN",
            (1, 1),
            (-1, -1),
            "RIGHT",
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
            BORDER,
        ),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [
                WHITE,
                VERY_LIGHT_BLUE,
            ],
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            3,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            3,
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

    for row_index, company_id in enumerate(
        row_company_ids,
        start=1,
    ):

        if (
            best_company is not None
            and company_id == best_company
        ):
            style_commands.append(
                (
                    "BACKGROUND",
                    (0, row_index),
                    (-1, row_index),
                    BEST_BG,
                )
            )

        elif (
            worst_company is not None
            and company_id == worst_company
        ):
            style_commands.append(
                (
                    "BACKGROUND",
                    (0, row_index),
                    (-1, row_index),
                    WORST_BG,
                )
            )

    table.setStyle(
        TableStyle(
            style_commands
        )
    )

    return table


# ============================================================================
# SECTOR PDF
# ============================================================================

def build_sector_report(
    sector_name,
    sector_companies,
    metrics,
    output_path,
    styles,
):
    """Build one sector PDF."""

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
    )

    story = []

    story.append(
        make_sector_header(
            sector_name,
            len(sector_companies),
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
            "Sector Summary — Median KPIs",
            styles["section"],
        )
    )

    story.append(
        make_sector_summary(
            metrics,
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
            "Companies in Sector — 8 Financial Metrics",
            styles["section"],
        )
    )

    story.append(
        make_company_table(
            metrics,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "Best/Worst highlighting is based on latest "
                "available ROE. Metrics represent the latest "
                "available company-level values in the N100 "
                "Financial Intelligence database. "
                "All monetary values are in ₹ crore unless "
                "stated otherwise."
            ),
            styles["footer"],
        )
    )

    document.build(
        story,
        onFirstPage=add_sector_page_number,
        onLaterPages=add_sector_page_number,
    )


def add_sector_page_number(
    canvas,
    document,
):
    """Add sector report footer."""

    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        6.5,
    )

    canvas.setFillColor(
        GREY_TEXT
    )

    canvas.drawCentredString(
        landscape(A4)[0] / 2,
        7 * mm,
        (
            "N100 Financial Intelligence Platform"
            f" | Page {document.page}"
        ),
    )

    canvas.restoreState()


# ============================================================================
# SECTOR BATCH
# ============================================================================

def generate_sector_reports(
    companies,
    profit_loss,
    ratios,
    growth,
    market_cap,
    sectors,
):
    """Generate one PDF for every broad sector in the database."""

    print("\n" + "=" * 72)
    print("SECTOR REPORT BATCH GENERATION")
    print("=" * 72)

    SECTOR_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    sector_names = (
        sectors["broad_sector"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    print(
        f"\nSectors found in database : "
        f"{len(sector_names)}"
    )

    generated = []
    failed = []

    styles = create_sector_styles()

    for index, sector_name in enumerate(
        sector_names,
        start=1,
    ):

        sector_companies = sectors[
            sectors["broad_sector"]
            .astype(str)
            .str.strip()
            == sector_name
        ].copy()

        metrics = prepare_company_metrics(
            sector_companies=sector_companies,
            profit_loss=profit_loss,
            ratios=ratios,
            growth=growth,
            market_cap=market_cap,
            companies=companies,
        )

        if metrics.empty:

            print(
                f"[SKIP] {sector_name}: "
                f"no company metrics"
            )

            continue

        filename = (
            f"{clean_filename(sector_name)}"
            "_report.pdf"
        )

        output_path = (
            SECTOR_DIR / filename
        )

        try:

            build_sector_report(
                sector_name=sector_name,
                sector_companies=sector_companies,
                metrics=metrics,
                output_path=output_path,
                styles=styles,
            )

            if not output_path.exists():
                raise FileNotFoundError(
                    f"Expected sector PDF was not created: "
                    f"{output_path}"
                )

            generated.append(sector_name)

            print(
                f"[{index}/{len(sector_names)}] "
                f"Generated {filename} "
                f"({len(metrics)} companies)"
            )

        except Exception as error:

            failed.append(
                (
                    sector_name,
                    str(error),
                )
            )

            print(
                f"[ERROR] {sector_name}: {error}"
            )

    return generated, failed


# ============================================================================
# VALIDATION
# ============================================================================

def validate_company_count(companies):
    """Validate the official company universe."""

    count = companies[
        "company_id"
    ].nunique()

    if count != EXPECTED_COMPANIES:
        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} companies "
            f"but found {count}."
        )


def count_generated_company_pdfs():
    """Count current company tearsheet PDFs."""

    if not TEARSHEET_DIR.exists():
        return 0

    return len(
        list(
            TEARSHEET_DIR.glob(
                "*_tearsheet.pdf"
            )
        )
    )


def count_generated_sector_pdfs():
    """Count current sector report PDFs."""

    if not SECTOR_DIR.exists():
        return 0

    return len(
        list(
            SECTOR_DIR.glob(
                "*_report.pdf"
            )
        )
    )


def validate_company_files(
    eligible_company_ids,
):
    """Validate that exactly the eligible company PDFs exist."""

    expected = {
        f"{company_id}_tearsheet.pdf"
        for company_id in eligible_company_ids
    }

    actual = {
        path.name
        for path in TEARSHEET_DIR.glob(
            "*_tearsheet.pdf"
        )
    }

    missing = sorted(
        expected - actual
    )

    unexpected = sorted(
        actual - expected
    )

    return missing, unexpected


def validate_sector_files(
    sector_names,
):
    """Validate that exactly the current sector PDFs exist."""

    expected = {
        f"{clean_filename(name)}_report.pdf"
        for name in sector_names
    }

    actual = {
        path.name
        for path in SECTOR_DIR.glob(
            "*_report.pdf"
        )
    }

    missing = sorted(
        expected - actual
    )

    unexpected = sorted(
        actual - expected
    )

    return missing, unexpected


# ============================================================================
# MAIN
# ============================================================================

def generate():
    """Run the complete Day 34 batch report generation."""

    print("=" * 72)
    print("SPRINT 5 — DAY 34 BATCH REPORT GENERATION")
    print("=" * 72)

    print("\nLoading database...")

    (
        companies,
        profit_loss,
        ratios,
        growth,
        market_cap,
        sectors,
    ) = load_day34_data()

    print(
        f"Official companies : "
        f"{companies['company_id'].nunique()}"
    )

    print(
        f"Sector records     : "
        f"{len(sectors)}"
    )

    print(
        f"Reports directory  : "
        f"{REPORTS_DIR}"
    )

    print(
        f"Tearsheet directory: "
        f"{TEARSHEET_DIR}"
    )

    print(
        f"Sector directory   : "
        f"{SECTOR_DIR}"
    )

    validate_company_count(
        companies
    )

    # ------------------------------------------------------------------
    # Clean stale outputs
    # ------------------------------------------------------------------

    print(
        "\nCleaning previous Day 34 PDF outputs..."
    )

    clean_previous_batch_outputs()

    # ------------------------------------------------------------------
    # Determine skipped companies
    # ------------------------------------------------------------------

    print(
        "\nChecking minimum 3-year data requirement..."
    )

    skipped = find_skipped_companies(
        companies,
        profit_loss,
    )

    save_skipped_companies(
        skipped
    )

    if skipped.empty:

        print(
            "Skipped companies  : 0"
        )

    else:

        print(
            f"Skipped companies  : {len(skipped)}"
        )

        for _, row in skipped.iterrows():

            print(
                f"  {row['company_id']} "
                f"({row['years_available']} years)"
            )

    # ------------------------------------------------------------------
    # Company tearsheets
    # ------------------------------------------------------------------

    generated_companies, company_failed = (
        generate_company_tearsheets(
            companies,
            skipped,
        )
    )

    eligible_company_ids = (
        companies[
            ~companies["company_id"].isin(
                skipped["company_id"]
            )
        ]["company_id"]
        .tolist()
    )

    missing_company_files, unexpected_company_files = (
        validate_company_files(
            eligible_company_ids
        )
    )

    # ------------------------------------------------------------------
    # Sector reports
    # ------------------------------------------------------------------

    sector_names = (
        sectors["broad_sector"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    generated_sectors, sector_failed = (
        generate_sector_reports(
            companies=companies,
            profit_loss=profit_loss,
            ratios=ratios,
            growth=growth,
            market_cap=market_cap,
            sectors=sectors,
        )
    )

    missing_sector_files, unexpected_sector_files = (
        validate_sector_files(
            sector_names
        )
    )

    # ------------------------------------------------------------------
    # Final counts
    # ------------------------------------------------------------------

    actual_company_pdfs = (
        count_generated_company_pdfs()
    )

    actual_sector_pdfs = (
        count_generated_sector_pdfs()
    )

    expected_company_pdfs = (
        len(eligible_company_ids)
    )

    expected_sector_pdfs = (
        len(sector_names)
    )

    company_pass = (
        generated_companies
        == expected_company_pdfs
        and actual_company_pdfs
        == expected_company_pdfs
        and not company_failed
        and not missing_company_files
        and not unexpected_company_files
    )

    sector_pass = (
        len(generated_sectors)
        == expected_sector_pdfs
        and actual_sector_pdfs
        == expected_sector_pdfs
        and not sector_failed
        and not missing_sector_files
        and not unexpected_sector_files
    )

    overall_pass = (
        company_pass
        and sector_pass
    )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    print("\n" + "=" * 72)
    print("DAY 34 GENERATION SUMMARY")
    print("=" * 72)

    print(
        f"Official companies       : "
        f"{companies['company_id'].nunique()}"
    )

    print(
        f"Eligible companies       : "
        f"{expected_company_pdfs}"
    )

    print(
        f"Skipped companies        : "
        f"{len(skipped)}"
    )

    print(
        f"Company PDFs generated   : "
        f"{generated_companies}"
    )

    print(
        f"Company PDFs on disk     : "
        f"{actual_company_pdfs}"
    )

    print(
        f"Company failures         : "
        f"{len(company_failed)}"
    )

    print(
        f"Sectors found            : "
        f"{expected_sector_pdfs}"
    )

    print(
        f"Sector PDFs generated    : "
        f"{len(generated_sectors)}"
    )

    print(
        f"Sector PDFs on disk      : "
        f"{actual_sector_pdfs}"
    )

    print(
        f"Sector failures          : "
        f"{len(sector_failed)}"
    )

    print(
        f"Skipped log              : "
        f"{SKIPPED_FILE}"
    )

    # ------------------------------------------------------------------
    # Validation details
    # ------------------------------------------------------------------

    if missing_company_files:

        print("\nMissing company PDFs:")

        for filename in missing_company_files:
            print(
                f"  {filename}"
            )

    if unexpected_company_files:

        print("\nUnexpected company PDFs:")

        for filename in unexpected_company_files:
            print(
                f"  {filename}"
            )

    if missing_sector_files:

        print("\nMissing sector PDFs:")

        for filename in missing_sector_files:
            print(
                f"  {filename}"
            )

    if unexpected_sector_files:

        print("\nUnexpected sector PDFs:")

        for filename in unexpected_sector_files:
            print(
                f"  {filename}"
            )

    if company_failed:

        print("\nCompany failures:")

        for company_id, error in company_failed:

            print(
                f"  {company_id}: {error}"
            )

    if sector_failed:

        print("\nSector failures:")

        for sector_name, error in sector_failed:

            print(
                f"  {sector_name}: {error}"
            )

    # ------------------------------------------------------------------
    # Final status
    # ------------------------------------------------------------------

    if overall_pass:

        print(
            "\nSTATUS: PASS"
        )

        print(
            "Day 34 batch generation completed "
            "with no missing or unexpected PDFs."
        )

    else:

        print(
            "\nSTATUS: REVIEW"
        )

        print(
            "Day 34 validation detected one or more "
            "generation or file-count problems."
        )

    print("=" * 72)

    return {
        "company_generated": generated_companies,
        "company_failed": company_failed,
        "sector_generated": len(
            generated_sectors
        ),
        "sector_failed": sector_failed,
        "skipped": skipped,
        "missing_company_files": missing_company_files,
        "unexpected_company_files": unexpected_company_files,
        "missing_sector_files": missing_sector_files,
        "unexpected_sector_files": unexpected_sector_files,
        "status": (
            "PASS"
            if overall_pass
            else "REVIEW"
        ),
    }


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    generate()