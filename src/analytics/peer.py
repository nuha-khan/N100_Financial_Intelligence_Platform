import sqlite3
import pandas as pd

DB_PATH = "data/nifty100.db"


def create_peer_percentiles_table(conn):

    conn.execute("""
    DROP TABLE IF EXISTS peer_percentiles;
    """)

    conn.execute("""
    CREATE TABLE peer_percentiles(

        company_id TEXT,

        peer_group_name TEXT,

        metric TEXT,

        value REAL,

        percentile_rank REAL,

        year INTEGER

    );
    """)

    conn.commit()

def load_tables():

    conn = sqlite3.connect(DB_PATH)

    financial_ratios = pd.read_sql(
        "SELECT * FROM financial_ratios",
        conn,
    )

    peer_groups = pd.read_sql(
        "SELECT * FROM peer_groups",
        conn,
    )

    conn.close()

    return financial_ratios, peer_groups

def merge_peer_groups():

    ratios, peer = load_tables()

    df = ratios.merge(

        peer,

        on="company_id",

        how="left"

    )

    return df

def compute_percentiles(df):

    metrics = {
        "return_on_equity_pct": True,
        "return_on_capital_employed_pct": True,
        "net_profit_margin_pct": True,
        "debt_to_equity": False,
        "free_cash_flow_cr": True,
        "pat_cagr_5y": True,
        "revenue_cagr_5y": True,
        "eps_cagr_5y": True,
        "interest_coverage": True,
        "asset_turnover": True,
    }

    results = []

    peer_df = df.dropna(subset=["peer_group_name"])

    for (peer_group, year), group in peer_df.groupby(
        ["peer_group_name", "year"]):

        if len(group) < 2:
            continue

        for metric, higher_is_better in metrics.items():

            ranks = group[metric].rank(
                pct=True,
                method="average"
            )

            if not higher_is_better:
                ranks = 1 - ranks

            temp = pd.DataFrame({

                "company_id": group["company_id"],

                "peer_group_name": peer_group,

                "metric": metric,

                "value": group[metric],

                "percentile_rank": ranks.round(4),

                "year": year,

            })

            results.append(temp)

    return pd.concat(results, ignore_index=True)

def save_peer_percentiles(df):

    conn = sqlite3.connect(DB_PATH)

    df.to_sql(
        "peer_percentiles",
        conn,
        if_exists="replace",
        index=False,
    )

    conn.commit()
    conn.close()

    print(f"Saved {len(df)} rows → peer_percentiles")

if __name__ == "__main__":

    percentile_df = compute_percentiles(merge_peer_groups())

    save_peer_percentiles(percentile_df)