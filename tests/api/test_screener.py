"""
Tests for Screener API routes.

Covers:
- Default screener endpoint
- Individual financial filters
- Multiple filters
- Response structure
- Alphabetical ordering
- Empty-result handling
- Screener templates
"""

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


# ---------------------------------------------------------------------
# SCREEN COMPANIES
# ---------------------------------------------------------------------

def test_screen_companies():
    """Test the default screener endpoint."""

    response = client.get("/api/v1/screener/")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "filters" in data
    assert "companies" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["filters"], dict)
    assert isinstance(data["companies"], list)


def test_screen_companies_response_structure():
    """Test the structure of screener company records."""

    response = client.get("/api/v1/screener/")

    assert response.status_code == 200

    data = response.json()

    if data["companies"]:
        company = data["companies"][0]

        expected_fields = {
            "company_id",
            "company_name",
            "broad_sector",
            "sub_sector",
            "year",
            "return_on_equity_pct",
            "debt_to_equity",
            "operating_profit_margin_pct",
            "net_profit_margin_pct",
            "interest_coverage",
            "asset_turnover",
            "revenue_cagr_5y",
        }

        assert expected_fields.issubset(company.keys())


def test_screen_companies_alphabetical_order():
    """Test that screener results are ordered by company name."""

    response = client.get("/api/v1/screener/")

    assert response.status_code == 200

    companies = response.json()["companies"]

    names = [
        company["company_name"]
        for company in companies
        if company["company_name"] is not None
    ]

    assert names == sorted(names)


# ---------------------------------------------------------------------
# INDIVIDUAL FILTERS
# ---------------------------------------------------------------------

def test_min_roe_filter():
    """Test minimum ROE filter."""

    response = client.get(
        "/api/v1/screener/",
        params={"min_roe": 15},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filters"]["min_roe"] == 15

    for company in data["companies"]:
        if company["return_on_equity_pct"] is not None:
            assert company["return_on_equity_pct"] >= 15


def test_max_debt_to_equity_filter():
    """Test maximum debt-to-equity filter."""

    response = client.get(
        "/api/v1/screener/",
        params={"max_debt_to_equity": 1},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filters"]["max_debt_to_equity"] == 1

    for company in data["companies"]:
        if company["debt_to_equity"] is not None:
            assert company["debt_to_equity"] <= 1


def test_min_revenue_cagr_filter():
    """Test minimum revenue CAGR filter."""

    response = client.get(
        "/api/v1/screener/",
        params={"min_revenue_cagr": 15},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filters"]["min_revenue_cagr"] == 15

    for company in data["companies"]:
        if company["revenue_cagr_5y"] is not None:
            assert company["revenue_cagr_5y"] >= 15


def test_min_opm_filter():
    """Test minimum operating profit margin filter."""

    response = client.get(
        "/api/v1/screener/",
        params={"min_opm": 20},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filters"]["min_opm"] == 20

    for company in data["companies"]:
        if company["operating_profit_margin_pct"] is not None:
            assert company["operating_profit_margin_pct"] >= 20


def test_min_npm_filter():
    """Test minimum net profit margin filter."""

    response = client.get(
        "/api/v1/screener/",
        params={"min_npm": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filters"]["min_npm"] == 10

    for company in data["companies"]:
        if company["net_profit_margin_pct"] is not None:
            assert company["net_profit_margin_pct"] >= 10


def test_min_interest_coverage_filter():
    """Test minimum interest coverage filter."""

    response = client.get(
        "/api/v1/screener/",
        params={"min_interest_coverage": 3},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filters"]["min_interest_coverage"] == 3

    for company in data["companies"]:
        if company["interest_coverage"] is not None:
            assert company["interest_coverage"] >= 3


def test_min_asset_turnover_filter():
    """Test minimum asset turnover filter."""

    response = client.get(
        "/api/v1/screener/",
        params={"min_asset_turnover": 1},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filters"]["min_asset_turnover"] == 1

    for company in data["companies"]:
        if company["asset_turnover"] is not None:
            assert company["asset_turnover"] >= 1


# ---------------------------------------------------------------------
# MULTIPLE FILTERS
# ---------------------------------------------------------------------

def test_multiple_screener_filters():
    """Test applying multiple filters simultaneously."""

    response = client.get(
        "/api/v1/screener/",
        params={
            "min_roe": 10,
            "max_debt_to_equity": 1.5,
            "min_opm": 10,
            "min_npm": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filters"]["min_roe"] == 10
    assert data["filters"]["max_debt_to_equity"] == 1.5
    assert data["filters"]["min_opm"] == 10
    assert data["filters"]["min_npm"] == 5

    for company in data["companies"]:
        if company["return_on_equity_pct"] is not None:
            assert company["return_on_equity_pct"] >= 10

        if company["debt_to_equity"] is not None:
            assert company["debt_to_equity"] <= 1.5

        if company["operating_profit_margin_pct"] is not None:
            assert company["operating_profit_margin_pct"] >= 10

        if company["net_profit_margin_pct"] is not None:
            assert company["net_profit_margin_pct"] >= 5


# ---------------------------------------------------------------------
# NO-RESULT FILTER
# ---------------------------------------------------------------------

def test_screener_no_results():
    """Test screener behavior when filters match no companies."""

    response = client.get(
        "/api/v1/screener/",
        params={
            "min_roe": 999999,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 0
    assert data["companies"] == []


# ---------------------------------------------------------------------
# FILTER RESPONSE
# ---------------------------------------------------------------------

def test_screener_default_filters():
    """Test that omitted filters are returned as None."""

    response = client.get("/api/v1/screener/")

    assert response.status_code == 200

    filters = response.json()["filters"]

    assert filters["min_roe"] is None
    assert filters["max_debt_to_equity"] is None
    assert filters["min_revenue_cagr"] is None
    assert filters["min_opm"] is None
    assert filters["min_npm"] is None
    assert filters["min_interest_coverage"] is None
    assert filters["min_asset_turnover"] is None


# ---------------------------------------------------------------------
# SCREENING TEMPLATES
# ---------------------------------------------------------------------

def test_get_screener_templates():
    """Test the predefined screening templates endpoint."""

    response = client.get("/api/v1/screener/templates")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "templates" in data

    assert data["count"] == 5
    assert len(data["templates"]) == 5


def test_screener_templates_response_structure():
    """Test the structure of screening templates."""

    response = client.get("/api/v1/screener/templates")

    assert response.status_code == 200

    templates = response.json()["templates"]

    for template in templates:
        assert "name" in template
        assert "description" in template
        assert "filters" in template

        assert isinstance(template["name"], str)
        assert isinstance(template["description"], str)
        assert isinstance(template["filters"], dict)


def test_screener_template_names():
    """Test that all expected screening templates are present."""

    response = client.get("/api/v1/screener/templates")

    assert response.status_code == 200

    templates = response.json()["templates"]

    names = {
        template["name"]
        for template in templates
    }

    expected_names = {
        "Quality Companies",
        "Growth Companies",
        "High Profitability",
        "Low Debt",
        "Balanced",
    }

    assert names == expected_names