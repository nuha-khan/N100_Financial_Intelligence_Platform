import os
import pandas as pd

from src.etl.normaliser import normalize_year, normalize_ticker


# Column-wise normalizers
NORMALIZERS = {"company_id": normalize_ticker,"year": normalize_year,}


def load_excel(file_path):
    """
    Load a single Excel file and apply column normalization.
    """

    print(f"\nLoading {os.path.basename(file_path)}...")

    df = pd.read_excel(file_path, skiprows=1)

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
    

if __name__ == "__main__":

    datasets = load_all_files()

    print("\nLoaded datasets:\n")

    for name, df in datasets.items():
        print(f"{name:<25} {len(df)} rows")