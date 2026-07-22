import os
import pandas as pd
import sqlite3
import time

from src.etl.normaliser import normalize_year, normalize_ticker


# Column-wise normalizers
NORMALIZERS = {"company_id": normalize_ticker,"year": normalize_year,}


def load_excel(file_path):
    """
    Load a single Excel file and apply column normalization.
    """

    print(f"\nLoading {os.path.basename(file_path)}...")

    # Raw financial datasets have an extra title row
    if "data/raw" in file_path.replace("\\", "/"):
        df = pd.read_excel(file_path, skiprows=1)

    # Supporting datasets already have headers
    else:
        df = pd.read_excel(file_path)

    for column, normalizer in NORMALIZERS.items():

        if column in df.columns:

            # print(f"\nBefore normalizing '{column}':")
            # print(df[column].head())

            df[column] = df[column].apply(normalizer)

            # print(f"\nAfter normalizing '{column}':")
            # print(df[column].head())

    # Remove rows where the year could not be normalized (e.g. TTM)
    if "year" in df.columns:

        original_rows = len(df)

        df = df.dropna(subset=["year"]).reset_index(drop=True)

        removed_rows = original_rows - len(df)

        if removed_rows > 0:
            print(f"Removed {removed_rows} rows with unparseable year values.")

    print(f"Loaded {len(df)} rows successfully.")

    return df


def load_all_files():
    """
    Load all Excel files from the raw and supporting folders.

    Returns:
        dict: Dictionary of DataFrames.
    """

    datasets = {}

    folders = [
        "data/raw",
        "data/supporting"
    ]

    for folder in folders:

        print(f"\nScanning {folder}...")

        for file in sorted(os.listdir(folder)):

            if file.endswith(".xlsx") and not file.startswith("~$"):

                file_path = os.path.join(folder, file)

                dataset_name = os.path.splitext(file)[0]

                datasets[dataset_name] = load_excel(file_path)

    print("\nTotal number of datasets loaded : ",len(datasets))
    return datasets

def create_database(db_path="data/nifty100.db"):
    """
    Create SQLite database and execute schema.sql.
    """

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)

    conn.execute("PRAGMA foreign_keys = ON;")

    with open("src/etl/schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    print(f"\nDatabase created successfully: {db_path}")

    return conn


def load_to_sqlite(datasets, conn):
    """
    Load all datasets into SQLite.
    """

    start = time.time()

    load_order = [
        "companies",
        "analysis",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "documents",
        "prosandcons",
        "sectors",
        "market_cap",
        "stock_prices",
        "financial_ratios",
        "peer_groups",
    ]

    for table in load_order:

        if table not in datasets:
            continue

        df = datasets[table]

        df.to_sql(table, conn, if_exists="replace", index=False,)

        db_rows = conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(
            f"Loaded {table:<20} "
            f"Source: {len(df):>5} rows | "
            f"SQLite: {db_rows:>5} rows"
        )

    conn.commit()

    runtime = round(time.time() - start, 2)

    print(f"\nSQLite loading completed in {runtime} seconds.")

    conn.close()


if __name__ == "__main__":

    datasets = load_all_files()

    print("\nLoaded datasets:\n")

    for name, df in datasets.items():
        print(f"{name:<25} {len(df)} rows")

    conn = create_database()

    load_to_sqlite(datasets, conn)