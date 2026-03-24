import pytest


@pytest.mark.asyncio
async def test_api_v1_discovery(client):
    response = await client.get("/api/v1/")
    assert response.status_code == 200
    data = response.json()
    assert "_links" in data
    assert "@context" in data
    assert data["@context"]["@vocab"] == "https://schema.org/"
    assert "message" in data
    rels = [link["rel"] for link in data["_links"]]
    assert "self" in rels
    assert "risk-by-coords" in rels
    assert "zones" in rels
    assert "subscriptions" in rels
