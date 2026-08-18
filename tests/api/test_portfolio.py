"""
Tests for Portfolio API routes.
"""


# ---------------------------------------------------------------------
# PORTFOLIO SNAPSHOT
# ---------------------------------------------------------------------

def test_get_portfolio_snapshot(client):
    response = client.get("/api/v1/portfolio/ABB")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert "company_name" in data
    assert "latest_market_data" in data
    assert "latest_financials" in data


def test_portfolio_snapshot_response_structure(client):
    response = client.get("/api/v1/portfolio/ABB")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert isinstance(data["company_name"], str)

    market = data["latest_market_data"]

    if market is not None:
        assert "date" in market
        assert "close_price" in market
        assert "adjusted_close" in market
        assert "volume" in market

    financials = data["latest_financials"]

    if financials is not None:
        assert "year" in financials
        assert "net_profit_margin_pct" in financials
        assert "operating_profit_margin_pct" in financials
        assert "return_on_equity_pct" in financials
        assert "debt_to_equity" in financials
        assert "interest_coverage" in financials
        assert "free_cash_flow_cr" in financials
        assert "earnings_per_share" in financials
        assert "dividend_payout_ratio_pct" in financials


def test_get_another_company_portfolio_snapshot(client):
    response = client.get("/api/v1/portfolio/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "company_name" in data


def test_get_invalid_company_portfolio_snapshot(client):
    response = client.get(
        "/api/v1/portfolio/INVALID_COMPANY"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------
# PRICE HISTORY
# ---------------------------------------------------------------------

def test_get_price_history(client):
    response = client.get("/api/v1/portfolio/ABB/prices")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert "company_name" in data
    assert "count" in data
    assert "prices" in data

    assert data["count"] == len(data["prices"])


def test_price_history_response_structure(client):
    response = client.get("/api/v1/portfolio/ABB/prices")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["prices"], list)

    if data["prices"]:
        price = data["prices"][0]

        assert "date" in price
        assert "open_price" in price
        assert "high_price" in price
        assert "low_price" in price
        assert "close_price" in price
        assert "volume" in price
        assert "adjusted_close" in price


def test_price_history_order(client):
    response = client.get("/api/v1/portfolio/ABB/prices")

    assert response.status_code == 200

    prices = response.json()["prices"]

    dates = [price["date"] for price in prices]

    assert dates == sorted(dates)


def test_get_another_company_price_history(client):
    response = client.get("/api/v1/portfolio/TCS/prices")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] == len(data["prices"])


def test_get_invalid_company_price_history(client):
    response = client.get(
        "/api/v1/portfolio/INVALID_COMPANY/prices"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------
# FINANCIAL HISTORY
# ---------------------------------------------------------------------

def test_get_financial_history(client):
    response = client.get("/api/v1/portfolio/ABB/financials")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert "company_name" in data
    assert "count" in data
    assert "financials" in data

    assert data["count"] == len(data["financials"])


def test_financial_history_response_structure(client):
    response = client.get("/api/v1/portfolio/ABB/financials")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["financials"], list)

    if data["financials"]:
        financial = data["financials"][0]

        assert "year" in financial
        assert "net_profit_margin_pct" in financial
        assert "operating_profit_margin_pct" in financial
        assert "return_on_equity_pct" in financial
        assert "debt_to_equity" in financial
        assert "interest_coverage" in financial
        assert "free_cash_flow_cr" in financial
        assert "capex_cr" in financial
        assert "earnings_per_share" in financial
        assert "book_value_per_share" in financial
        assert "dividend_payout_ratio_pct" in financial
        assert "total_debt_cr" in financial
        assert "cash_from_operations_cr" in financial


def test_financial_history_order(client):
    response = client.get("/api/v1/portfolio/ABB/financials")

    assert response.status_code == 200

    financials = response.json()["financials"]

    years = [financial["year"] for financial in financials]

    assert years == sorted(years)


def test_get_another_company_financial_history(client):
    response = client.get("/api/v1/portfolio/TCS/financials")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] == len(data["financials"])


def test_get_invalid_company_financial_history(client):
    response = client.get(
        "/api/v1/portfolio/INVALID_COMPANY/financials"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()