"""Global historical readings endpoint for regional and filtered queries."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import FireRiskReadingSchema
from app.services.history_service import get_historical_readings
from app.utils.constants import RISK_LEGEND_DATA
from app.utils.hateoas import create_links

router = APIRouter(prefix="/history", tags=["History"])


@router.get(
    "/",
    response_model=List[FireRiskReadingSchema],
    response_model_by_alias=True,
)
async def get_zones_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    geohashes: Optional[str] = Query(
        None,
        description="Comma-separated string of geohashes to filter by. If omitted, "
        "returns history for all regional zones.",
    ),
    start_date: Optional[datetime] = Query(
        None, description="Start date for the history (ISO 8601 format)."
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for the history (ISO 8601 format)."
    ),
):
    """Return historical fire-risk readings for regional or selected zones.

    This endpoint returns the normalized ``FireRiskReadingSchema`` collection
    enriched with legend metadata and HATEOAS links.
    """
    geohash_list = geohashes.split(",") if geohashes else None

    readings = await get_historical_readings(
        db, geohashes=geohash_list, start_date=start_date, end_date=end_date
    )

    if not readings:
        return []

    validated_readings = []
    for reading in readings:
        validated = FireRiskReadingSchema.model_validate(reading)
        validated.risk_legend = RISK_LEGEND_DATA
        validated.links = create_links(
            request,
            f"/risk/{validated.geohash}",
            others=[
                {"href": f"/risk/{validated.geohash}/history", "rel": "history"},
            ],
        )
        validated_readings.append(validated)

    return validated_readings
