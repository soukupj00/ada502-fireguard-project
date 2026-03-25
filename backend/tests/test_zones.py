from unittest.mock import patch

import pytest

from app.schemas import GeoJSONFeatureCollection, Link


@pytest.mark.asyncio
@patch("app.routers.zones.get_zones_geojson")
async def test_get_zones(mock_get_zones, client, mock_db_dep):
    from app.schemas import GeoJSONFeature, GeoJSONGeometry, GeoJSONProperties

    mock_get_zones.return_value = GeoJSONFeatureCollection(
        features=[
            GeoJSONFeature(
                geometry=GeoJSONGeometry(coordinates=[5.32, 60.39]),
                properties=GeoJSONProperties(geohash="u4pru", is_regional=True),
                _links=[Link(href="/api/v1/risk/u4pru", rel="risk-data")],
            )
        ],
        _links=[
            Link(href="/api/v1/zones/", rel="self"),
        ],
    )
    response = await client.get("/api/v1/zones/")
    assert response.status_code == 200
    data = response.json()
    assert "type" in data
    assert data["type"] == "FeatureCollection"
    assert "_links" in data
    assert "@context" in data
    assert data["@context"]["@vocab"] == "https://purl.org/geojson/vocab#"
    assert any(link["rel"] == "self" for link in data["_links"])
    assert not any(link["rel"] == "subscriptions" for link in data["_links"])

    # Check feature-level links
    feature = data["features"][0]
    assert "_links" in feature
    assert any(link["rel"] == "risk-data" for link in feature["_links"])
