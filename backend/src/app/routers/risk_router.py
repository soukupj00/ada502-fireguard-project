"""Risk endpoints for latest readings and historical time series."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_current_user_optional
from app.db.database import get_db
from app.schemas import FireRiskReadingSchema
from app.services.history_service import get_historical_readings_by_geohash
from app.services.risk_service import (
    get_latest_risk_by_coords,
    get_latest_risk_reading,
)
from app.utils.constants import RISK_LEGEND_DATA
from app.utils.hateoas import create_links

router = APIRouter(prefix="/risk", tags=["Fire Risk"])


@router.get(
    "/{geohash}/history",
    response_model=List[FireRiskReadingSchema],
    response_model_by_alias=True,
)
async def get_risk_history(
    request: Request,
    geohash: str,
    start_date: datetime | None = Query(
        None,
        description="Start date for the history (ISO 8601 format)."
        "Defaults to the beginning of time.",
    ),
    end_date: datetime | None = Query(
        None,
        description="End date for the history (ISO 8601 format)."
        "Defaults to the present.",
    ),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),  # PROTECTED: Requires authentication
):
    """Return historical fire-risk readings for one geohash.

    The endpoint is authenticated and returns a collection enriched with
    risk legend metadata and HATEOAS navigation links.
    """
    readings = await get_historical_readings_by_geohash(
        db, geohash, start_date, end_date
    )
    if not readings:
        # Return 200 OK with an empty list if no readings are found
        return []

    # Attach HATEOAS links to each reading in the collection
    validated_readings = []
    for reading in readings:
        validated = FireRiskReadingSchema.model_validate(reading)
        validated.risk_legend = RISK_LEGEND_DATA
        validated.links = create_links(
            request,
            f"/risk/{geohash}/history",
            others=[
                {"href": f"/risk/{geohash}", "rel": "latest"},
            ],
        )
        validated_readings.append(validated)

    return validated_readings


@router.get("/coords", response_model=FireRiskReadingSchema)
async def get_risk_by_coords(
    request: Request,
    latitude: float,
    longitude: float,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(
        get_current_user_optional
    ),  # Optional authentication
) -> FireRiskReadingSchema:
    """Return the latest fire-risk reading for a latitude/longitude pair.

    Authentication is optional; authenticated users also receive subscription
    and history links in the response.
    """
    reading = await get_latest_risk_by_coords(db, latitude, longitude)

    if not reading:
        raise HTTPException(
            status_code=404, detail="Risk data not found for this location"
        )

    # Attach HATEOAS links
    validated = FireRiskReadingSchema.model_validate(reading)
    validated.risk_legend = RISK_LEGEND_DATA
    # reading includes geohash attribute; use it to create a self link
    gh = getattr(reading, "geohash", None)
    self_path = (
        f"/risk/{gh}"
        if gh
        else f"/risk/coords?latitude={latitude}&longitude={longitude}"
    )

    other_links = [
        {"href": "/zones/", "rel": "zones"},
    ]
    if user:  # Only add protected links if user is authenticated
        other_links.append({"href": "/users/me/subscriptions/", "rel": "subscribe"})
        if gh:  # History link only makes sense if we have a geohash
            other_links.append({"href": f"/risk/{gh}/history", "rel": "history"})

    validated.links = create_links(
        request,
        self_path,
        others=other_links,
    )

    return validated


@router.get("/{geohash}", response_model=FireRiskReadingSchema)
async def get_risk_by_geohash(
    request: Request,
    geohash: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(
        get_current_user_optional
    ),  # Optional authentication
) -> FireRiskReadingSchema:
    """Return the latest fire-risk reading for a specific geohash.

    Authentication is optional; authenticated users receive additional HATEOAS
    links to subscription and history endpoints.
    """
    reading = await get_latest_risk_reading(db, geohash)

    if not reading:
        raise HTTPException(
            status_code=404, detail="Risk data not found for this location"
        )

    # Attach HATEOAS links
    validated = FireRiskReadingSchema.model_validate(reading)
    validated.risk_legend = RISK_LEGEND_DATA

    other_links = [
        {"href": "/zones/", "rel": "zones"},
    ]
    if user:  # Only add protected links if user is authenticated
        other_links.append({"href": "/users/me/subscriptions/", "rel": "subscribe"})
        other_links.append({"href": f"/risk/{geohash}/history", "rel": "history"})

    validated.links = create_links(
        request,
        f"/risk/{geohash}",
        others=other_links,
    )

    return validated
