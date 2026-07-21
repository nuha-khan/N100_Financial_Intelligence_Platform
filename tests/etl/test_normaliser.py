import pytest
from src.etl.normaliser import normalize_year,normalize_ticker

@pytest.mark.parametrize(
    "input_year, expected",
    [
        ("Dec 2012", 2012),
        ("Mar 2014", 2014),
        ("FY2023", 2023),
        ("2020", 2020),
        (" 2021 ", 2021),
        ("Mar-13", 2013),
        ("Mar-14", 2014),
        ("Mar-24", 2024),
        ("Dec 1999", 1999),
        ("FY2005", 2005),
        (None, None),
        ("", None),
        (" ", None),
        ("ABC", None),
        ("December", None),
        ("FY", None),
        ("Mar-", None),
        ("123", None),
        ("FY99", None),
        ("Random Text", None),
    ]
)
def test_normalize_year(input_year, expected):
    assert normalize_year(input_year) == expected

@pytest.mark.parametrize(
    "input_ticker, expected",
    [
        ("abb", "ABB"),
        ("ABB", "ABB"),
        (" Abb ", "ABB"),
        ("tcs", "TCS"),
        ("TCS", "TCS"),
        ("HdfcBank", "HDFCBANK"),
        (" infy ", "INFY"),
        ("reliance", "RELIANCE"),
        ("LT", "LT"),
        ("asianpaints", "ASIANPAINTS"),
        (None, None),
        ("", None),
        ("   ", None),
        ("\t", None),
        ("\n", None),
    ]
)
def test_normalize_ticker(input_ticker, expected):
    assert normalize_ticker(input_ticker) == expected