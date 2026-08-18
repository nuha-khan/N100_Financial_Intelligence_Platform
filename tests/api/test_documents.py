"""
Tests for Documents API routes.

Covers:
- All annual reports for a company
- Latest annual report
- Specific-year annual report
- Response structures
- Ordering
- Invalid companies
- Missing reports
"""

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


# ---------------------------------------------------------------------
# GET ALL DOCUMENTS
# ---------------------------------------------------------------------

def test_get_company_documents():
    """Test retrieving all annual reports for a company."""

    response = client.get("/api/v1/documents/RELIANCE")

    assert response.status_code == 200

    data = response.json()

    assert "company_id" in data
    assert "company_name" in data
    assert "count" in data
    assert "documents" in data

    assert data["company_id"] == "RELIANCE"
    assert isinstance(data["count"], int)
    assert isinstance(data["documents"], list)


def test_company_documents_response_structure():
    """Test the structure of annual report records."""

    response = client.get("/api/v1/documents/RELIANCE")

    assert response.status_code == 200

    data = response.json()

    if data["documents"]:
        document = data["documents"][0]

        assert "year" in document
        assert "annual_report" in document


def test_company_documents_order():
    """Test that documents are returned newest first."""

    response = client.get("/api/v1/documents/RELIANCE")

    assert response.status_code == 200

    documents = response.json()["documents"]

    years = [
        document["year"]
        for document in documents
        if document["year"] is not None
    ]

    assert years == sorted(years, reverse=True)


def test_get_another_company_documents():
    """Test documents for another valid company."""

    response = client.get("/api/v1/documents/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "documents" in data


def test_get_invalid_company_documents():
    """Test documents endpoint with an invalid company."""

    response = client.get("/api/v1/documents/INVALID_COMPANY")

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data


# ---------------------------------------------------------------------
# GET LATEST DOCUMENT
# ---------------------------------------------------------------------

def test_get_latest_company_document():
    """Test retrieving the latest annual report."""

    response = client.get("/api/v1/documents/RELIANCE/latest")

    assert response.status_code == 200

    data = response.json()

    assert "company_id" in data
    assert "company_name" in data
    assert "document" in data

    assert data["company_id"] == "RELIANCE"
    assert isinstance(data["document"], dict)


def test_latest_document_response_structure():
    """Test the structure of the latest document response."""

    response = client.get("/api/v1/documents/RELIANCE/latest")

    assert response.status_code == 200

    document = response.json()["document"]

    assert "year" in document
    assert "annual_report" in document


def test_latest_document_is_latest():
    """Test that the latest endpoint returns the newest available year."""

    all_response = client.get("/api/v1/documents/RELIANCE")
    latest_response = client.get("/api/v1/documents/RELIANCE/latest")

    assert all_response.status_code == 200
    assert latest_response.status_code == 200

    documents = all_response.json()["documents"]
    latest = latest_response.json()["document"]

    years = [
        document["year"]
        for document in documents
        if document["year"] is not None
    ]

    if years:
        assert latest["year"] == max(years)


def test_get_another_company_latest_document():
    """Test latest document for another valid company."""

    response = client.get("/api/v1/documents/TCS/latest")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert "document" in data


def test_get_invalid_company_latest_document():
    """Test latest document endpoint with an invalid company."""

    response = client.get(
        "/api/v1/documents/INVALID_COMPANY/latest"
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data


# ---------------------------------------------------------------------
# GET SPECIFIC YEAR DOCUMENT
# ---------------------------------------------------------------------

def test_get_specific_year_document():
    """Test retrieving an annual report for a specific year."""

    all_response = client.get("/api/v1/documents/RELIANCE")

    assert all_response.status_code == 200

    documents = all_response.json()["documents"]

    if documents:
        year = documents[0]["year"]

        response = client.get(
            f"/api/v1/documents/RELIANCE/{year}"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["company_id"] == "RELIANCE"
        assert "document" in data
        assert data["document"]["year"] == year


def test_specific_year_document_response_structure():
    """Test the structure of a specific-year document response."""

    all_response = client.get("/api/v1/documents/RELIANCE")

    assert all_response.status_code == 200

    documents = all_response.json()["documents"]

    if documents:
        year = documents[0]["year"]

        response = client.get(
            f"/api/v1/documents/RELIANCE/{year}"
        )

        assert response.status_code == 200

        document = response.json()["document"]

        assert "year" in document
        assert "annual_report" in document


def test_get_another_company_specific_year_document():
    """Test a specific-year document for another company."""

    all_response = client.get("/api/v1/documents/TCS")

    assert all_response.status_code == 200

    documents = all_response.json()["documents"]

    if documents:
        year = documents[0]["year"]

        response = client.get(
            f"/api/v1/documents/TCS/{year}"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["company_id"] == "TCS"
        assert data["document"]["year"] == year


def test_get_invalid_company_specific_year_document():
    """Test specific-year endpoint with an invalid company."""

    response = client.get(
        "/api/v1/documents/INVALID_COMPANY/2024"
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data


def test_get_missing_year_document():
    """Test a valid company with a year that has no report."""

    response = client.get(
        "/api/v1/documents/RELIANCE/1900"
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data