"""
Tests for Peer Intelligence API routes.
"""

# ---------------------------------------------------------------------
# GET PEER GROUPS
# ---------------------------------------------------------------------


def test_get_peer_groups(client):
    response = client.get("/api/v1/peers/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert "count" in data
    assert "peer_groups" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["peer_groups"], list)

    assert data["count"] == len(data["peer_groups"])
    assert data["count"] > 0


def test_peer_groups_response_structure(client):
    response = client.get("/api/v1/peers/")

    assert response.status_code == 200

    data = response.json()

    assert data["peer_groups"]

    peer = data["peer_groups"][0]

    assert isinstance(peer, dict)
    assert "company_id" in peer


# ---------------------------------------------------------------------
# GET PEERS FOR COMPANY
# ---------------------------------------------------------------------


def test_get_company_peers(client):
    response = client.get("/api/v1/peers/ABB")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)

    assert data["company_id"] == "ABB"
    assert "company_name" in data
    assert "peer_count" in data
    assert "peers" in data

    assert isinstance(data["company_name"], str)
    assert isinstance(data["peer_count"], int)
    assert isinstance(data["peers"], list)

    assert data["peer_count"] == len(data["peers"])


def test_get_another_company_peers(client):
    response = client.get("/api/v1/peers/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert isinstance(data["company_name"], str)
    assert isinstance(data["peers"], list)


def test_get_invalid_company_peers(client):
    response = client.get("/api/v1/peers/INVALID_COMPANY")

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data


# ---------------------------------------------------------------------
# GET PEER PERCENTILES
# ---------------------------------------------------------------------


def test_get_peer_percentiles(client):
    response = client.get("/api/v1/peers/ABB/percentiles")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)

    assert data["company_id"] == "ABB"
    assert "company_name" in data
    assert "percentiles" in data

    assert isinstance(data["company_name"], str)
    assert isinstance(data["percentiles"], list)


def test_get_another_company_percentiles(client):
    response = client.get("/api/v1/peers/TCS/percentiles")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert isinstance(data["company_name"], str)
    assert isinstance(data["percentiles"], list)


def test_get_invalid_company_percentiles(client):
    response = client.get(
        "/api/v1/peers/INVALID_COMPANY/percentiles"
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data


# ---------------------------------------------------------------------
# PEER PERCENTILE RESPONSE STRUCTURE
# ---------------------------------------------------------------------


def test_peer_percentiles_response_structure(client):
    response = client.get("/api/v1/peers/ABB/percentiles")

    assert response.status_code == 200

    data = response.json()

    assert set(
        ["company_id", "company_name", "percentiles"]
    ).issubset(data.keys())

    for percentile in data["percentiles"]:
        assert isinstance(percentile, dict)