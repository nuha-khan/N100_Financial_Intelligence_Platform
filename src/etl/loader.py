import os
import pandas as pd
import sqlite3
import time
from datetime import datetime

from src.etl.normaliser import normalize_year, normalize_ticker


# Column-wise normalizers
NORMALIZERS = {
    "company_id": normalize_ticker,
    "year": normalize_year,
}


def load_excel(file_path):
    """
    Load a single Excel file and apply column normalization.
    Remove exact duplicate rows.
    """

    print(f"\nLoading {os.path.basename(file_path)}...")

    # Raw financial datasets have an extra title row
    if "data/raw" in file_path.replace("\\", "/"):
        df = pd.read_excel(file_path, skiprows=1)
    else:
        df = pd.read_excel(file_path)

    # Apply column normalizers
    for column, normalizer in NORMALIZERS.items():
        if column in df.columns:
            df[column] = df[column].apply(normalizer)

    # Dataset-specific ticker corrections
    filename = os.path.basename(file_path).lower()

    if filename == "cashflow.xlsx" and "company_id" in df.columns:
        df["company_id"] = df["company_id"].replace({
            "AGTL": "ATGL"
        })

    # Remove rows where year could not be normalized
    if "year" in df.columns:
        original_rows = len(df)

        df = df.dropna(subset=["year"]).reset_index(drop=True)

        removed_rows = original_rows - len(df)

        if removed_rows > 0:
            print(
                f"Removed {removed_rows} rows "
                f"with unparseable year values."
            )

    # ---------------------------------------------------------
    # REMOVE EXACT DUPLICATE ROWS
    # ---------------------------------------------------------

    # Remove exact financial duplicates.
    # Ignore the source ID because duplicate records may have
    # different IDs but identical financial values.

    before_duplicates = len(df)

    dedup_columns = [
        column for column in df.columns
        if column != "id"
    ]

    df = df.drop_duplicates(
        subset=dedup_columns
    ).reset_index(drop=True)

    removed_duplicates = before_duplicates - len(df)

    if removed_duplicates > 0:
        print(
            f"Removed {removed_duplicates} exact duplicate rows."
        )

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

    print("\nTotal number of datasets loaded :", len(datasets))

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

    load_audit = []

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

        table_start = time.time()

        df = datasets[table]

        rows_in = len(df)

        df.to_sql(table, conn, if_exists="replace", index=False)

        db_rows = conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        runtime = round(time.time() - table_start, 3)

        load_audit.append({
            "table": table,
            "rows_in": rows_in,
            "rows_out": db_rows,
            "rejected": rows_in - db_rows,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "runtime_s": runtime
        })

        print(
            f"Loaded {table:<20} "
            f"Source: {rows_in:>5} rows | "
            f"SQLite: {db_rows:>5} rows"
        )

    conn.commit()

    os.makedirs("outputs", exist_ok=True)

    audit_df = pd.DataFrame(load_audit)

    audit_df.to_csv("outputs/load_audit.csv", index=False)

    runtime = round(time.time() - start, 2)

    print(f"\nSQLite loading completed in {runtime} seconds.")
    print("Load audit saved to outputs/load_audit.csv")

    conn.close()


if __name__ == "__main__":

    datasets = load_all_files()

    print("\nLoaded datasets:\n")

    for name, df in datasets.items():
        print(f"{name:<25} {len(df)} rows")

    conn = create_database()

    load_to_sqlite(datasets, conn)