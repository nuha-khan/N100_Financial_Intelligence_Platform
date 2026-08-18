# ============================================================
# Companies API Tests
# ============================================================


# ============================================================
# GET /api/v1/companies
# ============================================================

def test_get_companies(client):
    response = client.get("/api/v1/companies")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ============================================================
# GET /api/v1/companies/{company_id}
# ============================================================

def test_get_companies(client):
    response = client.get("/api/v1/companies")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "companies" in data

    assert isinstance(data["companies"], list)
    assert data["count"] == len(data["companies"])
    assert data["count"] > 0


def test_get_invalid_company(client):
    response = client.get("/api/v1/companies/INVALID_COMPANY")

    assert response.status_code == 404


# ============================================================
# GET /api/v1/companies/{company_id}/pl
# ============================================================

def test_get_company_profit_and_loss(client):
    response = client.get("/api/v1/companies/TCS/pl")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "count" in data
    assert "history" in data
    assert data["count"] == len(data["history"])


def test_get_company_profit_and_loss_with_date_filter(client):
    response = client.get(
        "/api/v1/companies/TCS/pl",
        params={
            "from_year": "2019-01",
            "to_year": "2024-12",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] == len(data["history"])

    years = [record["year"] for record in data["history"]]

    assert min(years) >= 2019
    assert max(years) <= 2024


def test_get_invalid_company_profit_and_loss(client):
    response = client.get(
        "/api/v1/companies/INVALID_COMPANY/pl"
    )

    assert response.status_code == 404


# ============================================================
# GET /api/v1/companies/{company_id}/bs
# ============================================================

def test_get_company_balance_sheet(client):
    response = client.get("/api/v1/companies/TCS/bs")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "count" in data
    assert "history" in data
    assert data["count"] == len(data["history"])


def test_get_company_balance_sheet_with_date_filter(client):
    response = client.get(
        "/api/v1/companies/TCS/bs",
        params={
            "from_year": "2019-01",
            "to_year": "2024-12",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == len(data["history"])

    years = [record["year"] for record in data["history"]]

    assert min(years) >= 2019
    assert max(years) <= 2024


def test_get_invalid_company_balance_sheet(client):
    response = client.get(
        "/api/v1/companies/INVALID_COMPANY/bs"
    )

    assert response.status_code == 404


# ============================================================
# GET /api/v1/companies/{company_id}/cashflow
# ============================================================

def test_get_company_cashflow(client):
    response = client.get(
        "/api/v1/companies/TCS/cashflow"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "count" in data
    assert "history" in data
    assert data["count"] == len(data["history"])


def test_get_company_cashflow_with_date_filter(client):
    response = client.get(
        "/api/v1/companies/TCS/cashflow",
        params={
            "from_year": "2019-01",
            "to_year": "2024-12",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == len(data["history"])

    years = [record["year"] for record in data["history"]]

    assert min(years) >= 2019
    assert max(years) <= 2024


def test_get_invalid_company_cashflow(client):
    response = client.get(
        "/api/v1/companies/INVALID_COMPANY/cashflow"
    )

    assert response.status_code == 404


# ============================================================
# Response Structure Tests
# ============================================================

def test_profit_and_loss_response_structure(client):
    response = client.get("/api/v1/companies/TCS/pl")

    assert response.status_code == 200

    record = response.json()["history"][0]

    required_fields = [
        "year",
        "sales",
        "expenses",
        "operating_profit",
        "opm_percentage",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_percentage",
        "net_profit",
        "eps",
        "dividend_payout",
    ]

    for field in required_fields:
        assert field in record


def test_balance_sheet_response_structure(client):
    response = client.get("/api/v1/companies/TCS/bs")

    assert response.status_code == 200

    record = response.json()["history"][0]

    required_fields = [
        "year",
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
    ]

    for field in required_fields:
        assert field in record


def test_cashflow_response_structure(client):
    response = client.get(
        "/api/v1/companies/TCS/cashflow"
    )

    assert response.status_code == 200

    record = response.json()["history"][0]

    required_fields = [
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ]

    for field in required_fields:
        assert field in record