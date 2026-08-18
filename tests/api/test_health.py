"""
Tests for Health API routes.
"""

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


# ---------------------------------------------------------------------
# SYSTEM HEALTH
# ---------------------------------------------------------------------

def test_health_check():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "db_row_counts" in data


def test_health_check_response_structure():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "db_row_counts" in data
    assert "uptime_seconds" in data
    assert "version" in data

    assert data["status"] == "ok"
    assert isinstance(data["db_row_counts"], dict)


def test_health_check_contains_all_tables():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    db_row_counts = data["db_row_counts"]

    expected_tables = {
    "analysis",
    "balancesheet",
    "cashflow",
    "companies",
    "company_growth_metrics",
    "documents",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "peer_percentiles",
}

    assert expected_tables.issubset(db_row_counts.keys())


def test_health_check_table_counts_are_non_negative():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    db_row_counts = response.json()["db_row_counts"]

    for table, count in db_row_counts.items():
        assert isinstance(table, str)
        assert isinstance(count, int)
        assert count >= 0


# ---------------------------------------------------------------------
# COMPANY FINANCIAL HEALTH
# ---------------------------------------------------------------------

def test_get_company_health():
    response = client.get("/api/v1/health/RELIANCE")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "RELIANCE"
    assert "year" in data
    assert "roe" in data
    assert "roce" in data
    assert "revenue_cagr_5y" in data
    assert "debt_to_equity" in data
    assert "health_score" in data
    assert "health_band" in data


def test_company_health_response_structure():
    response = client.get("/api/v1/health/RELIANCE")

    assert response.status_code == 200

    data = response.json()

    expected_keys = {
        "company_id",
        "year",
        "roe",
        "roce",
        "revenue_cagr_5y",
        "debt_to_equity",
        "health_score",
        "health_band",
    }

    assert set(data.keys()) == expected_keys


def test_company_health_score_range():
    response = client.get("/api/v1/health/RELIANCE")

    assert response.status_code == 200

    data = response.json()

    assert 0 <= data["health_score"] <= 100


def test_company_health_band():
    response = client.get("/api/v1/health/RELIANCE")

    assert response.status_code == 200

    data = response.json()

    assert data["health_band"] in {
        "Excellent",
        "Good",
        "Average",
        "Weak",
        "Poor",
    }


def test_company_health_band_matches_score():
    response = client.get("/api/v1/health/RELIANCE")

    assert response.status_code == 200

    data = response.json()
    score = data["health_score"]

    if score >= 80:
        expected_band = "Excellent"
    elif score >= 60:
        expected_band = "Good"
    elif score >= 40:
        expected_band = "Average"
    elif score >= 20:
        expected_band = "Weak"
    else:
        expected_band = "Poor"

    assert data["health_band"] == expected_band


def test_company_health_case_insensitive():
    upper_response = client.get("/api/v1/health/RELIANCE")
    lower_response = client.get("/api/v1/health/reliance")

    assert upper_response.status_code == 200
    assert lower_response.status_code == 200

    upper_data = upper_response.json()
    lower_data = lower_response.json()

    assert upper_data["company_id"] == lower_data["company_id"]
    assert upper_data["health_score"] == lower_data["health_score"]
    assert upper_data["health_band"] == lower_data["health_band"]


def test_get_another_company_health():
    response = client.get("/api/v1/health/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert 0 <= data["health_score"] <= 100
    assert data["health_band"] in {
        "Excellent",
        "Good",
        "Average",
        "Weak",
        "Poor",
    }


# ---------------------------------------------------------------------
# INVALID COMPANY
# ---------------------------------------------------------------------

def test_get_invalid_company_health():
    response = client.get("/api/v1/health/INVALID_COMPANY")

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data
    assert data["detail"] == "Company 'INVALID_COMPANY' not found"