"""Zone service that assembles GeoJSON views over monitored zones and risk."""

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CurrentFireRisk, MonitoredZone
from app.schemas import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    GeoJSONProperties,
)
from app.utils.constants import RISK_LEGEND_DATA
from app.utils.hateoas import create_links


async def get_zones_geojson(
    db: AsyncSession, request: Request
) -> GeoJSONFeatureCollection:
    """
    Get all regional monitored zones in GeoJSON format.

    This implementation fetches the latest risk data from the CurrentFireRisk table,
    which is updated periodically. This avoids complex queries on the historical
    FireRiskReading table.

    Args:
        db: Database session.
        request: FastAPI Request object for dynamic links.
    """
    # 1. Fetch zones
    zone_query = select(MonitoredZone).where(MonitoredZone.is_regional == True)  # noqa: E712

    zone_result = await db.execute(zone_query)
    zones = zone_result.scalars().all()

    if not zones:
        return GeoJSONFeatureCollection(
            features=[],
            risk_legend=RISK_LEGEND_DATA,
            links=create_links(
                request,
                "/zones/",
            ),
        )

    # 2. Fetch current risks for these zones
    geohashes = [z.geohash for z in zones]
    risk_query = select(CurrentFireRisk).where(CurrentFireRisk.geohash.in_(geohashes))
    risk_result = await db.execute(risk_query)
    risks = risk_result.scalars().all()

    # Map geohash -> risk object
    risk_map = {r.geohash: r for r in risks}

    features = []
    for zone in zones:
        risk_data = risk_map.get(zone.geohash)
        risk_score = risk_data.risk_score if risk_data else None
        risk_category = risk_data.risk_category if risk_data else None

        feature = GeoJSONFeature(
            geometry=GeoJSONGeometry(coordinates=[zone.center_lon, zone.center_lat]),
            properties=GeoJSONProperties(
                geohash=zone.geohash,
                name=zone.name,
                is_regional=zone.is_regional,
                risk_score=risk_score,
                risk_category=risk_category,
                last_updated=zone.last_updated,
            ),
            links=create_links(
                request,
                f"/risk/{zone.geohash}",
                others=[{"href": f"/risk/{zone.geohash}/history", "rel": "history"}],
            ),
        )
        # Fix: the create_links rel=self will be /risk/{geohash}, we want rel=risk-data
        if feature.links:
            for link in feature.links:
                if link.rel == "self":
                    link.rel = "risk-data"

        features.append(feature)

    collection_links = create_links(
        request,
        "/zones/",
    )

    return GeoJSONFeatureCollection(
        features=features, risk_legend=RISK_LEGEND_DATA, links=collection_links
    )
