from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import GeoJSONFeatureCollection
from app.services.zone_service import get_zones_geojson

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("/", response_model=GeoJSONFeatureCollection, response_model_by_alias=True)
async def get_zones(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """
    Get all regional monitored zones in GeoJSON format.
    """
    return await get_zones_geojson(db, request)
