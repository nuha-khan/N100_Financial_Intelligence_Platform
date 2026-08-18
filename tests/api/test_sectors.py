"""
Tests for Sectors API endpoints.
"""

# ---------------------------------------------------------------------
# GET ALL SECTORS
# ---------------------------------------------------------------------

def test_get_sectors(client):
    response = client.get("/api/v1/sectors/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert "count" in data
    assert "sectors" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["sectors"], list)

    assert data["count"] == len(data["sectors"])
    assert data["count"] > 0


# ---------------------------------------------------------------------
# GET ALL SECTORS - RESPONSE STRUCTURE
# ---------------------------------------------------------------------

def test_sectors_response_structure(client):
    response = client.get("/api/v1/sectors/")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "sectors" in data

    if data["sectors"]:
        sector = data["sectors"][0]

        expected_fields = {
            "broad_sector",
            "company_count",
            "median_roe",
            "median_pe",
            "median_de",
        }

        assert expected_fields.issubset(sector.keys())

# ---------------------------------------------------------------------
# GET SINGLE COMPANY SECTOR
# ---------------------------------------------------------------------

def test_get_company_sector(client):
    response = client.get("/api/v1/sectors/TCS")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)

    assert data["company_id"] == "TCS"
    assert "broad_sector" in data
    assert "sub_sector" in data
    assert "index_weight_pct" in data
    assert "market_cap_category" in data


# ---------------------------------------------------------------------
# GET SINGLE COMPANY SECTOR - DIFFERENT COMPANY
# ---------------------------------------------------------------------

def test_get_another_company_sector(client):
    response = client.get("/api/v1/sectors/ABB")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "ABB"
    assert data["broad_sector"] is not None
    assert data["sub_sector"] is not None


# ---------------------------------------------------------------------
# INVALID COMPANY
# ---------------------------------------------------------------------

def test_get_invalid_company_sector(client):
    response = client.get("/api/v1/sectors/INVALID_COMPANY")

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data
    assert "INVALID_COMPANY" in data["detail"]


# ---------------------------------------------------------------------
# SECTOR SUMMARY
# ---------------------------------------------------------------------

def test_get_sector_summary(client):
    response = client.get("/api/v1/sectors/summary/all")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert "count" in data
    assert "sectors" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["sectors"], list)

    assert data["count"] == len(data["sectors"])
    assert data["count"] > 0


# ---------------------------------------------------------------------
# SECTOR SUMMARY - RESPONSE STRUCTURE
# ---------------------------------------------------------------------

def test_sector_summary_response_structure(client):
    response = client.get("/api/v1/sectors/summary/all")

    assert response.status_code == 200

    data = response.json()

    if data["sectors"]:
        sector = data["sectors"][0]

        expected_fields = {
            "broad_sector",
            "company_count",
            "total_index_weight_pct",
        }

        assert expected_fields.issubset(sector.keys())


# ---------------------------------------------------------------------
# SECTOR SUMMARY - VALID VALUES
# ---------------------------------------------------------------------

def test_sector_summary_values(client):
    response = client.get("/api/v1/sectors/summary/all")

    assert response.status_code == 200

    data = response.json()

    for sector in data["sectors"]:
        assert isinstance(sector["broad_sector"], str)
        assert sector["company_count"] > 0
        assert sector["total_index_weight_pct"] is not None