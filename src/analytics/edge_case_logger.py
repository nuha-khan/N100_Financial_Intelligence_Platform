import os

OUTPUT_DIR = "outputs"


def categorize_anomaly(source_value, engine_value):
    """
    Categorize anomaly according to Sprint 2 rules.
    """

    if source_value is None:
        return "Data Source Issue"

    if abs(source_value) < 1:
        return "Data Source Issue"

    return "Formula Discrepancy"


def log_ratio_edge_cases(merged_df, ratios_df):
    """
    Compare calculated ROE/ROCE against source values
    and generate outputs/ratio_edge_cases.log.
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filepath = os.path.join(
        OUTPUT_DIR,
        "ratio_edge_cases.log",
    )

    with open(filepath, "w", encoding="utf-8") as log:

        log.write("=" * 80 + "\n")
        log.write("SPRINT 2 - RATIO EDGE CASE REPORT\n")
        log.write("=" * 80 + "\n\n")

        anomalies = 0

        # ratios_df already contains company_name,
        # roe_percentage and roce_percentage.
        comparison = ratios_df

        for _, row in comparison.iterrows():

            # -----------------------------
            # ROE comparison
            # -----------------------------

            source = row["roe_percentage"]
            engine = row["return_on_equity_pct"]

            if (
                source is not None
                and engine is not None
                and abs(source - engine) > 5
            ):

                anomalies += 1

                category = categorize_anomaly(
                    source,
                    engine,
                )

                log.write(f"Company : {row['company_id']}\n")
                log.write(f"Year    : {int(row['year'])}\n")
                log.write("Metric  : ROE\n")
                log.write(f"Source  : {source}\n")
                log.write(f"Engine  : {engine}\n")
                log.write(
                    f"Difference : {round(abs(source-engine),2)}\n"
                )
                log.write(f"Category : {category}\n")
                log.write("-" * 80 + "\n")

            # -----------------------------
            # ROCE comparison
            # -----------------------------

            source = row["roce_percentage"]
            engine = row["return_on_capital_employed_pct"]

            if (
                source is not None
                and engine is not None
                and abs(source - engine) > 5
            ):

                anomalies += 1

                category = categorize_anomaly(
                    source,
                    engine,
                )

                log.write(f"Company : {row['company_id']}\n")
                log.write(f"Year    : {int(row['year'])}\n")
                log.write("Metric  : ROCE\n")
                log.write(f"Source  : {source}\n")
                log.write(f"Engine  : {engine}\n")
                log.write(
                    f"Difference : {round(abs(source-engine),2)}\n"
                )
                log.write(f"Category : {category}\n")
                log.write("-" * 80 + "\n")

        log.write("\n")
        log.write("=" * 80 + "\n")
        log.write(f"Total anomalies detected : {anomalies}\n")

    print(f"Saved anomaly report → {filepath}")