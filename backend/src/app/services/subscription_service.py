from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CurrentFireRisk, MonitoredZone, UserSubscription
from app.schemas import (
    SubscriptionRequest,
    SubscriptionResponse,
    UserSubscriptionListResponse,
)
from app.utils.grid import get_geohash, get_geohash_center


async def subscribe_to_location_logic(
    db: AsyncSession, payload: SubscriptionRequest, user_id: str
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
        )

    return SubscriptionResponse(
        geohash=geohash,
        status="pending" if current_risk is None else "active",
        message="Successfully subscribed to location.",
        current_risk=current_risk,
    )


async def get_user_subscriptions_logic(
    db: AsyncSession, user_id: str
) -> UserSubscriptionListResponse:
    """
    Get all geohashes a user is subscribed to.
    """
    result = await db.execute(
        select(UserSubscription.geohash).where(UserSubscription.user_id == user_id)
    )
    geohashes = result.scalars().all()
    return UserSubscriptionListResponse(geohashes=list(geohashes))
