"""Zone discovery and regional history endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import GeoJSONFeatureCollection
from app.services.history_service import get_historical_readings
from app.services.zone_service import get_zones_geojson
from app.utils.constants import RISK_LEGEND_DATA
from app.utils.hateoas import create_links

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("/", response_model=GeoJSONFeatureCollection, response_model_by_alias=True)
async def get_zones(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """Return all regional monitored zones as a GeoJSON feature collection."""
    # The actual logic is in get_zones_geojson, which now adds the history link
    return await get_zones_geojson(db, request)


@router.get(
    "/history",
    response_model=List[dict],
    response_model_by_alias=True,
)
async def get_zones_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    geohashes: Optional[str] = Query(
        None,
        description="Comma-separated string of geohashes to filter by. "
        "If omitted, returns history for all regional zones.",
    ),
    start_date: Optional[str] = Query(
        None, description="Start date for the history (ISO 8601 format)."
    ),
    end_date: Optional[str] = Query(
        None, description="End date for the history (ISO 8601 format)."
    ),
):
    """Return historical risk readings for regional zones or selected geohashes.

    The endpoint is public. If ``geohashes`` is omitted, data is scoped to
    predefined regional zones.
    """
    geohash_list = geohashes.split(",") if geohashes else None

    # Parse date strings into datetimes. Query string encoding can turn '+' into
    # spaces, so normalize by replacing a space before a timezone offset back to '+'.
    def _parse_date(s: Optional[str]):
        if not s:
            return None
        # Fix cases where '+00:00' becomes ' 00:00' in query strings
        s_fixed = s.replace(" ", "+")
        try:
            return datetime.fromisoformat(s_fixed)
        except Exception:
            # Let FastAPI return a 422 with a helpful error message
            from fastapi import HTTPException

            raise HTTPException(status_code=422, detail=f"Invalid date format: {s}")

    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)

    readings = await get_historical_readings(
        db=db, geohashes=geohash_list, start_date=start_dt, end_date=end_dt
    )

    if not readings:
        return []

    features: list[dict] = []
    for reading in readings:
        gh = getattr(reading, "geohash", None) or getattr(
            reading, "location_name", None
        )
        props = {
            "geohash": gh,
            "name": getattr(reading, "name", None),
            "is_regional": True,
            "risk_score": getattr(reading, "risk_score", None),
            "risk_category": getattr(reading, "risk_category", None),
            "last_updated": getattr(reading, "updated_at", None),
        }

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    getattr(reading, "longitude", None),
                    getattr(reading, "latitude", None),
                ],
            },
            "properties": props,
            "risk_legend": RISK_LEGEND_DATA,
            "_links": create_links(
                request,
                f"/risk/{gh}",
                others=[{"href": f"/risk/{gh}/history", "rel": "history-single-zone"}],
            ),
        }
        features.append(feature)

    return features
