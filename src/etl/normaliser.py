"""
normaliser.py

Helper functions to standardize raw data before validation
and loading into the SQLite database.
"""

import re

# Pattern to extract a 4-digit year
YEAR_PATTERN = r"(19|20)\d{2}"

# Pattern to extract a 2-digit year (e.g. Mar-13)
SHORT_YEAR_PATTERN = r"-(\d{2})$"


def normalize_year(year):
    """
    Normalize different year formats.

    Supported formats:
        Dec 2012  -> 2012
        Mar 2024  -> 2024
        FY2023    -> 2023
        Mar-13    -> 2013
        Mar-24    -> 2024
        2022      -> 2022

    Returns:
        int  : Normalized year
        None : If no valid year is found
    """

    if year is None:
        return None

    year = str(year).strip()

    # First try to find a 4-digit year
    match = re.search(YEAR_PATTERN, year)

    if match:
        return int(match.group())

    # Then try formats like Mar-13
    match = re.search(SHORT_YEAR_PATTERN, year)

    if match:
        short_year = int(match.group(1))

        # Assuming dataset years belong to the 2000s
        return 2000 + short_year

    return None


def normalize_ticker(ticker):
    """
    Standardize company ticker symbols.

    Example:
        ' abb ' -> 'ABB'
        'tcs'   -> 'TCS'

    Returns:
        str : Normalized ticker
        None : If ticker is empty
    """

    if ticker is None:
        return None

    ticker = str(ticker).strip().upper()

    if ticker == "":
        return None

    return ticker