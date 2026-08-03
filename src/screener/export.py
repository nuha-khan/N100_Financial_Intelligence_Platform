import os
import pandas as pd


OUTPUT_FILE = "outputs/screener_output.xlsx"


def export_screeners(results):
    """
    Export all screener presets into one Excel workbook.

    Parameters
    ----------
    results : dict
        {
            preset_name: dataframe
        }
    """

    os.makedirs("outputs", exist_ok=True)

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
    ) as writer:

        for preset, df in results.items():

            export_df = df.sort_values(
                "composite_quality_score",
                ascending=False,
            )

            export_df.to_excel(
                writer,
                sheet_name=preset[:31],      # Excel sheet limit
                index=False,
            )

    print(f"\nSaved -> {OUTPUT_FILE}")