import sqlite3
import pandas as pd
import yaml
from src.screener.scoring import compute_composite_score
from src.screener.export import export_screeners
from src.screener.format_excel import colour_screeners

DB_PATH = "data/nifty100.db"
CONFIG_PATH = "config/screener_config.yaml"

def load_data():
    """
    Load required tables from SQLite.
    """

    conn = sqlite3.connect(DB_PATH)

    financial_ratios = pd.read_sql(
        "SELECT * FROM financial_ratios",
        conn,
    )

    companies = pd.read_sql(
        "SELECT * FROM companies",
        conn,
    )

    sectors = pd.read_sql(
        "SELECT * FROM sectors",
        conn,
    )

    market_cap = pd.read_sql(
        "SELECT * FROM market_cap",
        conn,
    )

    conn.close()

    return financial_ratios, companies, sectors, market_cap

def load_config():
    """
    Load screener YAML.
    """

    with open(CONFIG_PATH, "r") as file:
        config = yaml.safe_load(file)

    return config

def merge_tables(
    financial_ratios,
    companies,
    sectors,
    market_cap,
):
    """
    Merge all required tables.
    """

    df = financial_ratios.merge(
        companies,
        left_on="company_id",
        right_on="id",
        how="left",
    )

    df = df.merge(
        sectors.drop(columns="id"),
        on="company_id",
        how="left",
    )

    df = df.merge(
        market_cap.drop(columns="id"),
        on=["company_id", "year"],
        how="left",
    )

    return df

def apply_filters(df, filters):
    """
    Apply screener filters from YAML configuration.
    """

    filtered = df.copy()

    # ROE filter
    if "roe_min" in filters:
        filtered = filtered[
            filtered["return_on_equity_pct"] >= filters["roe_min"]
        ]

    # Revenue CAGR filter
    if "revenue_cagr_5y_min" in filters:
        filtered = filtered[
            filtered["revenue_cagr_5y"] >= filters["revenue_cagr_5y_min"]
        ]

    # PAT CAGR filter
    if "pat_cagr_5y_min" in filters:
        filtered = filtered[
            filtered["pat_cagr_5y"] >= filters["pat_cagr_5y_min"]
        ]

    # Free Cash Flow filter
    if "free_cash_flow_min" in filters:
        filtered = filtered[
            filtered["free_cash_flow_cr"] >= filters["free_cash_flow_min"]
        ]

    # Debt-to-Equity
    if "debt_to_equity_max" in filters:

        financials = (
            filtered["broad_sector"]
            .fillna("")
            .str.lower()
            .eq("financials")
        )

        filtered = filtered[
            financials |
            (filtered["debt_to_equity"] <= filters["debt_to_equity_max"])
        ]

    # Interest Coverage
    if "interest_coverage_min" in filters:

        icr = filtered["interest_coverage"].fillna(float("inf"))

        filtered = filtered[
            icr >= filters["interest_coverage_min"]
        ]

    # Market Cap
    if "market_cap_min" in filters:
        filtered = filtered[
            filtered["market_cap_crore"] >= filters["market_cap_min"]
        ]

    # PE
    if "pe_max" in filters:
        filtered = filtered[
            filtered["pe_ratio"] <= filters["pe_max"]
        ]

    # PB
    if "pb_max" in filters:
        filtered = filtered[
            filtered["pb_ratio"] <= filters["pb_max"]
        ]

    # Dividend Yield
    if "dividend_yield_min" in filters:
        filtered = filtered[
            filtered["dividend_yield_pct"] >= filters["dividend_yield_min"]
        ]

    # Dividend Payout
    if "dividend_payout_ratio_max" in filters:
        filtered = filtered[
            filtered["dividend_payout_ratio_pct"]
            <= filters["dividend_payout_ratio_max"]
        ]

    return filtered.sort_values(
        "composite_quality_score",
        ascending=False,
    )

def run_preset(preset_name):
    """
    Run one screener preset from YAML.
    """

    ratios, companies, sectors, market = load_data()

    df = merge_tables(
        ratios,
        companies,
        sectors,
        market,
    )
    df = compute_composite_score(df)
    config = load_config()

    if preset_name not in config:
        raise ValueError(
            f"Preset '{preset_name}' not found."
        )

    filters = config[preset_name]

    result = apply_filters(
        df,
        filters,
    )

    return result

if __name__ == "__main__":

    presets = [
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    ]

    all_results = {}

    for preset in presets:

        result = run_preset(preset)

        all_results[preset] = result

        print(f"\n{preset.upper()}")
        print("-" * 40)

        print(f"Unique Companies : {result['company_id'].nunique()}")

        print(f"Company-Year Rows: {len(result)}")

    export_screeners(all_results)
    colour_screeners("outputs/screener_output.xlsx")