from unittest.mock import patch

import pytest
from conftest import MOCK_GEOHASH


@pytest.mark.asyncio
@patch("app.routers.risk_router.get_latest_risk_reading")
async def test_get_risk_by_geohash_success(
    mock_get_risk, client, mock_db_dep, mock_risk_reading
):
    mock_get_risk.return_value = mock_risk_reading
    response = await client.get(f"/api/v1/risk/{MOCK_GEOHASH}")
    assert response.status_code == 200
    data = response.json()
    assert data["geohash"] == MOCK_GEOHASH
    assert "_links" in data
    assert "@context" in data
    assert data["@context"]["@vocab"] == "https://schema.org/"
    rels = [link["rel"] for link in data["_links"]]
    assert "self" in rels
    assert "subscribe" in rels
    assert "zones" in rels


@pytest.mark.asyncio
@patch("app.routers.risk_router.get_latest_risk_reading")
async def test_get_risk_by_geohash_not_found(mock_get_risk, client, mock_db_dep):
    mock_get_risk.return_value = None
    response = await client.get("/api/v1/risk/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
@patch("app.routers.risk_router.get_latest_risk_by_coords")
async def test_get_risk_by_coords_success(
    mock_get_risk, client, mock_db_dep, mock_risk_reading
):
    mock_get_risk.return_value = mock_risk_reading
    response = await client.get(
        "/api/v1/risk/coords", params={"latitude": 60.39, "longitude": 5.32}
    )
    assert response.status_code == 200
    data = response.json()
    assert "_links" in data
    assert "@context" in data
    assert data["@context"]["@vocab"] == "https://schema.org/"
    rels = [link["rel"] for link in data["_links"]]
    assert "self" in rels
    assert "subscribe" in rels
    assert "zones" in rels


@pytest.mark.asyncio
async def test_get_risk_by_coords_missing_params(client, mock_db_dep):
    response = await client.get("/api/v1/risk/coords", params={"latitude": 60.39})
    assert response.status_code == 422
