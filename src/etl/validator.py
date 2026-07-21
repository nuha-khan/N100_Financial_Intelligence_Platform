"""
validator.py

Data Quality (DQ) validation rules for the ETL pipeline.
"""
import os
import pandas as pd
from src.etl.loader import load_all_files

load_audit = []

def create_failure_records(failed_rows,rule,severity,table_name,columns,message):
    """
    Create a standardized DataFrame containing validation failures.

    Parameters
    ----------
    failed_rows : pandas.DataFrame
        Rows that failed validation.

    rule : str
        DQ rule ID (e.g. DQ-01).

    severity : str
        CRITICAL or WARNING.

    table_name : str
        Name of the table being validated.

    columns : list
        Column(s) involved in the validation.

    message : str
        Description of the validation failure.

    Returns
    -------
    pandas.DataFrame
    """

    failure_columns = ["rule","severity","table","row","column","value","message",]

    if failed_rows.empty:
        return pd.DataFrame(columns=failure_columns)

    values = []

    for _, row in failed_rows[columns].iterrows():
        row_values = [str(value) for value in row.tolist()]
        values.append(" | ".join(row_values))

    values = pd.Series(values)

    failures = pd.DataFrame({
        "rule": rule,
        "severity": severity,
        "table": table_name,
        "row": failed_rows.index,
        "column": ", ".join(columns),
        "value": values.values,
        "message": message,
    })

    return failures

def create_load_audit(rule,severity,table_name,rows_checked,rows_flagged,message,):
    """
    Create audit records for load_audit.csv
    """

    return pd.DataFrame([{
        "rule": rule,
        "severity": severity,
        "table": table_name,
        "rows_checked": rows_checked,
        "rows_flagged": rows_flagged,
        "message": message
    }])

def check_pk_uniqueness(df, table_name, columns):
    """
    DQ-01

    Check that the primary key column contains unique values.
    """

    failed_rows = df[df.duplicated(subset=columns, keep=False)]

    if failed_rows.empty:
        print("✅ DQ-01 Passed")
    else:
        print(f"❌ DQ-01 Failed [{table_name}] ({len(failed_rows)} duplicate rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-01",
        severity="CRITICAL",
        table_name=table_name,
        columns=columns,
        message="Duplicate primary key found.",
    )


def check_company_year_pk(df, table_name):
    """
    DQ-02

    Check that every (company_id, year)
    combination is unique.
    """

    failed_rows = df[df.duplicated(subset=["company_id", "year"], keep=False)]

    if failed_rows.empty:
        print("✅ DQ-02 Passed")
    else:
        print(f"❌ DQ-02 Failed [{table_name}] ({len(failed_rows)} duplicate rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-02",
        severity="CRITICAL",
        table_name=table_name,
        columns=["company_id", "year"],
        message="Duplicate company-year combination found.",
    )

def check_fk_integrity(df, companies_df, table_name):
    """
    DQ-03

    Check that every company_id exists
    in the companies table.
    """

    valid_company_ids = set(companies_df["id"])

    failed_rows = df[
        ~df["company_id"].isin(valid_company_ids)
    ]

    if failed_rows.empty:
        print("✅ DQ-03 Passed")
    else:
        print(f"❌ DQ-03 Failed [{table_name}] ({len(failed_rows)} invalid rows)")
   
    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-03",
        severity="CRITICAL",
        table_name=table_name,
        columns=["company_id"],
        message="Company ID does not exist in companies table.",
    )
def check_balance_sheet(df, table_name):
    """
    DQ-04

    Check that Total Assets and Total Liabilities
    balance within 1%.
    """

    difference_percent = (
        (df["total_assets"] - df["total_liabilities"]).abs()
        / df["total_assets"].replace(0, pd.NA)
    )

    failed_rows = df[difference_percent > 0.01]

    if failed_rows.empty:
        print(f"✅ DQ-04 Passed [{table_name}]")
    else:
        print(f"❌ DQ-04 Failed [{table_name}] ({len(failed_rows)} invalid rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-04",
        severity="WARNING",
        table_name=table_name,
        columns=["company_id", "year"],
        message="Balance sheet difference exceeds 1%.",
    )

def check_opm(df, table_name):
    """
    DQ-05

    Check that Operating Profit Margin (OPM)
    is calculated correctly.
    """

    calculated_opm = (
    (
        df["operating_profit"]
        / df["sales"].replace(0, float("nan"))
    ) * 100).round()

    failed_rows = df[(calculated_opm - df["opm_percentage"]).abs() > 1].copy()

    if failed_rows.empty:
        print(f"✅ DQ-05 Passed [{table_name}]")
    else:
        print(f"❌ DQ-05 Failed [{table_name}] ({len(failed_rows)} invalid rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-05",
        severity="WARNING",
        table_name=table_name,
        columns=["company_id", "year"],
        message="OPM percentage does not match calculated value.",
    )

def check_positive_sales(df, table_name):
    """
    DQ-06

    Check that sales are greater than zero.
    """

    failed_rows = df[(df["sales"].isna()) | (df["sales"] <= 0)]

    if failed_rows.empty:
        print(f"✅ DQ-06 Passed [{table_name}]")
    else:
        print(f"❌ DQ-06 Failed [{table_name}] ({len(failed_rows)} invalid rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-06",
        severity="WARNING",
        table_name=table_name,
        columns=["company_id", "year", "sales"],
        message="Sales must be greater than zero.",
    )

def check_year_format(df, table_name):
    """
    DQ-07

    Validate year/date fields after normalization.

    Applies only to datasets that contain
    a year, Year or date column.
    """

    # Financial tables
    if "year" in df.columns:
        values = pd.to_numeric(df["year"], errors="coerce")
        validation_columns = ["company_id", "year"]

        failed_rows = df[values.isna() | (values < 1900) | (values > 2100)]

    # Documents table
    elif "Year" in df.columns:
        values = pd.to_numeric(df["Year"], errors="coerce")
        validation_columns = ["company_id", "Year"]

        failed_rows = df[values.isna() | (values < 1900) | (values > 2100)]

    # Stock Prices table
    elif "date" in df.columns:

        dates = pd.to_datetime(df["date"], errors="coerce")

        validation_columns = ["company_id", "date"]

        failed_rows = df[dates.isna()]

    else:
        # Rule not applicable
        return pd.DataFrame()

    if failed_rows.empty:
        print(f"✅ DQ-07 Passed [{table_name}]")
    else:
        print(f"❌ DQ-07 Failed [{table_name}] ({len(failed_rows)} invalid rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-07",
        severity="CRITICAL",
        table_name=table_name,
        columns=validation_columns,
        message="Invalid year/date format.",
    )

def check_net_cash_flow(df, table_name):
    """
    DQ-09

    Check that:

    Operating Activity +
    Investing Activity +
    Financing Activity

    equals

    Net Cash Flow.
    """

    calculated_net_cash = (
        df["operating_activity"] +
        df["investing_activity"] +
        df["financing_activity"]
    )

    difference = (calculated_net_cash - df["net_cash_flow"]).abs()

    failed_rows = df[difference > 1]

    if failed_rows.empty:
        print(f"✅ DQ-09 Passed [{table_name}]")
    else:
        print(f"❌ DQ-09 Failed [{table_name}] ({len(failed_rows)} invalid rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-09",
        severity="WARNING",
        table_name=table_name,
        columns=[
            "company_id",
            "year",
            "net_cash_flow",
        ],
        message="Net cash flow does not match calculated value.",
    )

def check_tax_percentage(df, table_name):
    """
    DQ-11

    Check that the tax percentage matches:

    ((Profit Before Tax - Net Profit)
    / Profit Before Tax) * 100
    """

    valid_rows = df[df["profit_before_tax"] > 0].copy()

    calculated_tax = (
        (valid_rows["profit_before_tax"] - valid_rows["net_profit"]) / valid_rows["profit_before_tax"]* 100
        ).round()

    difference = (calculated_tax - valid_rows["tax_percentage"]).abs()

    failed_rows = valid_rows[difference > 1]

    if failed_rows.empty:
        print(f"✅ DQ-11 Passed [{table_name}]")
    else:
        print(f"❌ DQ-11 Failed [{table_name}] ({len(failed_rows)} invalid rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-11",
        severity="WARNING",
        table_name=table_name,
        columns=[
            "company_id",
            "year",
            "tax_percentage",
        ],
        message="Tax percentage does not match calculated value.",
    )

def check_dividend_cap(df, table_name):
    """
    DQ-12

    Check that dividend payout
    does not exceed 100%.
    """

    failed_rows = df[df["dividend_payout"] > 200]

    if failed_rows.empty:
        print(f"✅ DQ-12 Passed [{table_name}]")
    else:
        print(f"❌ DQ-12 Failed [{table_name}] ({len(failed_rows)} invalid rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-12",
        severity="WARNING",
        table_name=table_name,
        columns=[
            "company_id",
            "year",
            "dividend_payout",
        ],
        message="Dividend payout exceeds 100%.",
    )

def check_annual_report_url(df, table_name):
    """
    DQ-13

    Check that Annual Report URLs
    are valid.
    """

    failed_rows = df[
    df["Annual_Report"].isna()
    |
    (
        df["Annual_Report"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["", "null"])
    )
    |
    (
        ~df["Annual_Report"]
        .astype(str)
        .str.startswith(("http://", "https://"))
    )]

    if failed_rows.empty:
        print(f"✅ DQ-13 Passed [{table_name}]")
    else:
        print(f"❌ DQ-13 Failed [{table_name}] ({len(failed_rows)} invalid rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-13",
        severity="WARNING",
        table_name=table_name,
        columns=[
            "company_id",
            "Year",
            "Annual_Report",
        ],
        message="Invalid Annual Report URL.",
    )

def check_eps_sign(df, table_name):
    """
    DQ-14

    Check that EPS sign matches
    Net Profit sign.
    """

    failed_rows = df[
        ((df["net_profit"] > 0) & (df["eps"] < 0))
        |
        ((df["net_profit"] < 0) & (df["eps"] > 0))
    ]

    if failed_rows.empty:
        print(f"✅ DQ-14 Passed [{table_name}]")
    else:
        print(f"❌ DQ-14 Failed [{table_name}] ({len(failed_rows)} invalid rows)")

    return create_failure_records(
        failed_rows=failed_rows,
        rule="DQ-14",
        severity="WARNING",
        table_name=table_name,
        columns=[
            "company_id",
            "year",
            "net_profit",
            "eps",
        ],
        message="EPS sign does not match Net Profit sign.",
    )

def check_bse_ase_balance(df, table_name):
    """
    DQ-15

    Strict Balance Sheet Equality Check

    Rule:
        total_assets == total_liabilities

    Severity:
        INFO

    Action:
        Record results in load_audit.csv only.
    """

    failed_rows = df[df["total_assets"] != df["total_liabilities"]
]

    if failed_rows.empty:
        print(f"✅ DQ-15 Passed [{table_name}]")

    else:
        print(f"ℹ️ DQ-15 [{table_name}] ({len(failed_rows)} rows with unequal Assets and Liabilities)")

    return create_load_audit(
        rule="DQ-15",
        severity="INFO",
        table_name=table_name,
        rows_checked=len(df),
        rows_flagged=len(failed_rows),
        message="Strict Assets == Liabilities equality check."
    )

def check_coverage(datasets):
    """
    DQ-16

    Coverage Check

    Rule:
        Each company should have at least 5 years of
        Profit & Loss, Balance Sheet and Cash Flow data.

    Severity:
        WARNING
    """

    failures = []

    tables = {
        "profitandloss": datasets["profitandloss"],
        "balancesheet": datasets["balancesheet"],
        "cashflow": datasets["cashflow"],
    }

    for table_name, df in tables.items():

        coverage = (
            df.groupby("company_id")["year"]
            .nunique()
            .reset_index(name="years_available")
        )

        failed = coverage[coverage["years_available"] < 5]

        if failed.empty:
            print(f"✅ DQ-16 Passed [{table_name}]")

        else:
            print(f"❌ DQ-16 Failed [{table_name}] ({len(failed)} companies)")

        failures.append(
            create_failure_records(
                failed_rows=failed,
                rule="DQ-16",
                severity="WARNING",
                table_name=table_name,
                columns=["company_id", "years_available"],
                message="Company has fewer than 5 years of financial history."
            )
        )

    return pd.concat(failures, ignore_index=True)

def run_all_validations(datasets):
    """
    Run all implemented Data Quality checks.
    """

    failures = []
    audit = []

    failures.append(check_pk_uniqueness(datasets["companies"], "companies", ["id"]))
    failures.append(check_company_year_pk(datasets["profitandloss"], "profitandloss"))
    
    fk_tables = [
    "analysis",
    "balancesheet",
    "cashflow",
    "documents",
    "profitandloss",
    "prosandcons",
    ]
    for table in fk_tables:
        failures.append(check_fk_integrity(datasets[table],datasets["companies"],table))

    failures.append(check_balance_sheet(datasets["balancesheet"],"balancesheet"))
    failures.append(check_opm(datasets["profitandloss"],"profitandloss"))
    failures.append(check_positive_sales(datasets["profitandloss"],"profitandloss"))
    failures.append(check_net_cash_flow(datasets["cashflow"],"cashflow"))
    failures.append(check_tax_percentage(datasets["profitandloss"],"profitandloss"))
    failures.append(check_dividend_cap(datasets["profitandloss"],"profitandloss"))
    failures.append(check_annual_report_url(datasets["documents"],"documents"))
    failures.append(check_eps_sign(datasets["profitandloss"],"profitandloss"))

    for table_name, df in datasets.items():
        failures.append(check_year_format(df, table_name))

    audit.append(check_bse_ase_balance(datasets["balancesheet"],"balancesheet"))

    failures.append(check_coverage(datasets))

    validation_failures = pd.concat(failures, ignore_index=True)
    load_audit = pd.concat(audit, ignore_index=True)

    return validation_failures, load_audit


if __name__ == "__main__":
    datasets = load_all_files()
    
    validation_failures, load_audit = run_all_validations(datasets)
    # print("\n===== Validation Failures =====")
    # print(validation_failures)
    # print("\n===== Audit Records =====")
    # print(load_audit)
 
    validation_failures.to_csv("outputs/validation_failures.csv",index=False,mode="w")
    load_audit.to_csv("outputs/load_audit.csv",index=False,mode="w")

    print("\nValidation failures saved to output/validation_failures.csv")
    print("\nLoad audit saved to output/load_audit.csv")