"""
Tests for Valuation API routes.
"""

import pytest


# ---------------------------------------------------------------------
# LATEST VALUATION
# ---------------------------------------------------------------------

def test_get_company_valuation(client):
    response = client.get("/api/v1/valuation/ABB")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert "company_name" in data
    assert "valuation" in data


def test_company_valuation_response_structure(client):
    response = client.get("/api/v1/valuation/ABB")

    assert response.status_code == 200

    data = response.json()
    valuation = data["valuation"]

    assert "company_id" in valuation
    assert "year" in valuation
    assert "market_cap_crore" in valuation
    assert "enterprise_value_crore" in valuation
    assert "pe_ratio" in valuation
    assert "pb_ratio" in valuation
    assert "ev_ebitda" in valuation
    assert "dividend_yield_pct" in valuation


def test_get_another_company_valuation(client):
    response = client.get("/api/v1/valuation/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "company_name" in data
    assert data["valuation"]["company_id"] == "TCS"


def test_get_invalid_company_valuation(client):
    response = client.get("/api/v1/valuation/INVALID_COMPANY")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------
# VALUATION HISTORY
# ---------------------------------------------------------------------

def test_get_valuation_history(client):
    response = client.get("/api/v1/valuation/ABB/history")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert "company_name" in data
    assert "count" in data
    assert "history" in data

    assert data["count"] == len(data["history"])


def test_valuation_history_response_structure(client):
    response = client.get("/api/v1/valuation/ABB/history")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["history"], list)

    if data["history"]:
        record = data["history"][0]

        assert "year" in record
        assert "market_cap_crore" in record
        assert "enterprise_value_crore" in record
        assert "pe_ratio" in record
        assert "pb_ratio" in record
        assert "ev_ebitda" in record
        assert "dividend_yield_pct" in record


def test_valuation_history_order(client):
    response = client.get("/api/v1/valuation/ABB/history")

    assert response.status_code == 200

    history = response.json()["history"]

    years = [record["year"] for record in history]

    assert years == sorted(years)


def test_get_another_company_valuation_history(client):
    response = client.get("/api/v1/valuation/TCS/history")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] == len(data["history"])


def test_get_invalid_company_valuation_history(client):
    response = client.get(
        "/api/v1/valuation/INVALID_COMPANY/history"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------
# VALUATION SUMMARY
# ---------------------------------------------------------------------

def test_get_valuation_summary(client):
    response = client.get("/api/v1/valuation/ABB/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert "company_name" in data
    assert "valuation" in data
    assert "growth" in data


def test_valuation_summary_response_structure(client):
    response = client.get("/api/v1/valuation/ABB/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert isinstance(data["company_name"], str)

    if data["valuation"] is not None:
        valuation = data["valuation"]

        assert "year" in valuation
        assert "market_cap_crore" in valuation
        assert "enterprise_value_crore" in valuation
        assert "pe_ratio" in valuation
        assert "pb_ratio" in valuation
        assert "ev_ebitda" in valuation
        assert "dividend_yield_pct" in valuation

    if data["growth"] is not None:
        growth = data["growth"]

        assert "compounded_sales_growth" in growth
        assert "compounded_profit_growth" in growth
        assert "stock_price_cagr" in growth
        assert "roe" in growth


def test_get_invalid_company_valuation_summary(client):
    response = client.get(
        "/api/v1/valuation/INVALID_COMPANY/summary"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()