from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import FireRiskReadingSchema
from app.services.risk_service import (
    get_latest_risk_by_coords,
    get_latest_risk_reading,
)
from app.utils.hateoas import create_links

router = APIRouter(prefix="/risk", tags=["Fire Risk"])


@router.get("/coords", response_model=FireRiskReadingSchema)
async def get_risk_by_coords(
    request: Request,
    latitude: float,
    longitude: float,
    db: AsyncSession = Depends(get_db),
) -> FireRiskReadingSchema:
    """
    Get the latest fire risk reading for a location by coordinates.
    """
    reading = await get_latest_risk_by_coords(db, latitude, longitude)

    if not reading:
        raise HTTPException(
            status_code=404, detail="Risk data not found for this location"
        )

    # Attach HATEOAS links
    validated = FireRiskReadingSchema.model_validate(reading)
    # reading includes geohash attribute; use it to create a self link
    gh = getattr(reading, "geohash", None)
    self_path = (
        f"/risk/{gh}"
        if gh
        else f"/risk/coords?latitude={latitude}&longitude={longitude}"
    )

    validated.links = create_links(
        request,
        self_path,
        others=[
            {"href": "/users/me/subscriptions/", "rel": "subscribe"},
            {"href": "/zones/", "rel": "zones"},
        ],
    )

    return validated


@router.get("/{geohash}", response_model=FireRiskReadingSchema)
async def get_risk_by_geohash(
    request: Request, geohash: str, db: AsyncSession = Depends(get_db)
) -> FireRiskReadingSchema:
    """
    Get the latest fire risk reading for a specific geohash.
    """
    reading = await get_latest_risk_reading(db, geohash)

    if not reading:
        raise HTTPException(
            status_code=404, detail="Risk data not found for this location"
        )

    # Attach HATEOAS links
    validated = FireRiskReadingSchema.model_validate(reading)
    validated.links = create_links(
        request,
        f"/risk/{geohash}",
        others=[
            {"href": "/users/me/subscriptions/", "rel": "subscribe"},
            {"href": "/zones/", "rel": "zones"},
        ],
    )

    return validated
