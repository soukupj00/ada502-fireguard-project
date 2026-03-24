from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CurrentFireRisk, MonitoredZone, UserSubscription
from app.schemas import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    GeoJSONProperties,
    SubscriptionRequest,
    SubscriptionResponse,
)
from app.utils.grid import get_geohash, get_geohash_center
from app.utils.hateoas import create_links


async def subscribe_to_location_logic(
    db: AsyncSession, payload: SubscriptionRequest, user_id: str, request: Request
) -> SubscriptionResponse:
    """
    Subscribe to a location for fire risk monitoring.

    If the location is not already monitored, it will be added to the monitored zones.
    Links the subscription to the authenticated user.
    """
    # Determine geohash from payload
    if payload.geohash:
        geohash = payload.geohash
    elif payload.latitude is not None and payload.longitude is not None:
        # Calculate geohash with precision 5 (approx 4.9km x 4.9km)
        geohash = get_geohash(payload.latitude, payload.longitude, precision=5)
    else:
        raise HTTPException(
            status_code=400,
            detail="Either geohash or both latitude and longitude must be provided.",
        )

    # 1. Check or Create the MonitoredZone
    result = await db.execute(
        select(MonitoredZone).where(MonitoredZone.geohash == geohash)
    )
    existing_zone = result.scalars().first()

    if not existing_zone:
        center_lat, center_lon = get_geohash_center(geohash)
        new_zone = MonitoredZone(
            geohash=geohash,
            center_lat=center_lat,
            center_lon=center_lon,
            is_regional=False,  # User subscription
            name=f"User Subscription {geohash}",
        )
        db.add(new_zone)
        # Flush to ensure the zone exists before linking the subscription
        await db.flush()

    # 2. Check current risk to return it immediately
    current_risk = None
    risk_result = await db.execute(
        select(CurrentFireRisk).where(CurrentFireRisk.geohash == geohash)
    )
    latest_risk = risk_result.scalars().first()
    if latest_risk:
        current_risk = latest_risk.ttf

    # Create HATEOAS links back to the subscription list
    links = create_links(
        request,
        "/users/me/subscriptions/",
        others=[
            {"href": f"/risk/{geohash}", "rel": "risk-data"},
            {"href": "/users/me/subscriptions/", "rel": "collection"},
        ],
    )

    # 3. Create the UserSubscription mapping
    try:
        user_sub = UserSubscription(user_id=user_id, geohash=geohash)
        db.add(user_sub)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # The user is already subscribed to this geohash
        return SubscriptionResponse(
            geohash=geohash,
            status="active",
            message="Location is already being monitored by you.",
            current_risk=current_risk,
            links=links,
        )

    return SubscriptionResponse(
        geohash=geohash,
        status="pending" if current_risk is None else "active",
        message="Successfully subscribed to location.",
        current_risk=current_risk,
        links=links,
    )


async def get_user_subscriptions_logic(
    db: AsyncSession, user_id: str, request: Request
) -> GeoJSONFeatureCollection:
    """
    Get all zones a user is subscribed to in GeoJSON-LD format.
    Includes the latest risk data if available.
    """
    # 1. Find all geohashes the user is subscribed to
    sub_query = select(UserSubscription.geohash).where(
        UserSubscription.user_id == user_id
    )
    sub_result = await db.execute(sub_query)
    user_geohashes = sub_result.scalars().all()

    if not user_geohashes:
        return GeoJSONFeatureCollection(
            features=[],
            links=create_links(request, "/users/me/subscriptions/"),
        )

    # 2. Fetch the corresponding MonitoredZones
    zone_query = select(MonitoredZone).where(MonitoredZone.geohash.in_(user_geohashes))
    zone_result = await db.execute(zone_query)
    zones = zone_result.scalars().all()

    # 3. Fetch the current risks for these zones
    risk_query = select(CurrentFireRisk).where(
        CurrentFireRisk.geohash.in_(user_geohashes)
    )
    risk_result = await db.execute(risk_query)
    risks = risk_result.scalars().all()

    # Map geohash -> risk object
    risk_map = {r.geohash: r for r in risks}

    # 4. Construct the GeoJSON Feature Collection
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
            links=create_links(request, f"/risk/{zone.geohash}", others=[]),
        )
        # Fix: the create_links rel=self will be /risk/{geohash}, we want rel=risk-data
        if feature.links:
            for link in feature.links:
                if link.rel == "self":
                    link.rel = "risk-data"

        features.append(feature)

    collection_links = create_links(request, "/users/me/subscriptions/")

    return GeoJSONFeatureCollection(features=features, links=collection_links)
