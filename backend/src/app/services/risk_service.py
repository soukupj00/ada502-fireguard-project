"""Risk service helpers for current-risk lookups and fallback scoring."""

from datetime import datetime, timezone
from typing import Optional

import pygeohash as pgh
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CurrentFireRisk
from app.schemas import FireRiskRequest, FireRiskResponse


def calculate_fire_risk_logic(payload: FireRiskRequest) -> FireRiskResponse:
    """Compute a simplified fire-risk score from weather parameters.

    This is a lightweight fallback/illustrative calculation, not the
    production intelligence pipeline model.
    """
    # Simple placeholder logic for risk calculation
    # In a real application, this would involve a complex model
    risk_score = (
        (payload.temperature / 100)
        + (payload.humidity / 100)
        - (payload.wind_speed / 100)
    )
    risk_score = max(0, min(1, risk_score))  # Clamp between 0 and 1

    time_to_flashover = 600 * (1 - risk_score)  # Inverse relationship

    if risk_score > 0.75:
        recommendation = (
            "High risk: Evacuation may be necessary. Monitor official alerts."
        )
    elif risk_score > 0.5:
        recommendation = (
            "Moderate risk: Be prepared. "
            "Clear flammable materials from around your home."
        )
    else:
        recommendation = "Low risk: Stay informed and practice fire safety."

    # Return a response that matches the FireRiskResponse model
    return FireRiskResponse(
        risk_score=risk_score,
        time_to_flashover=time_to_flashover,
        recommendation=recommendation,
        timestamp=datetime.now(timezone.utc),
    )


async def get_latest_risk_reading(
    db: AsyncSession, geohash: str
) -> Optional[CurrentFireRisk]:
    """
    Get the latest fire risk reading for a
    specific geohash from the CurrentFireRisk table.
    """
    query = select(CurrentFireRisk).where(CurrentFireRisk.geohash == geohash)
    result = await db.execute(query)
    return result.scalars().first()


async def get_latest_risk_by_coords(
    db: AsyncSession, latitude: float, longitude: float
) -> Optional[CurrentFireRisk]:
    """
    Get the latest fire risk reading for given coordinates by converting to a
    geohash and reusing the geohash lookup.
    """
    # Assuming precision 5 for geohash as used elsewhere
    geohash = pgh.encode(latitude, longitude, precision=5)
    return await get_latest_risk_reading(db, geohash)
