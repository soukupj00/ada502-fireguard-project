import logging
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MonitoredZone
from app.utils.constants import ANALYTICS_CITIES

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _CandidateZone:
    geohash: str
    center_lat: float
    center_lon: float


def _distance_sq(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return (lat1 - lat2) ** 2 + (lon1 - lon2) ** 2


def _pick_analytics_zones(zones: Iterable[_CandidateZone]) -> list[str]:
    remaining = list(zones)
    chosen: list[str] = []

    for city in ANALYTICS_CITIES:
        if not remaining:
            break

        city_lat = city["latitude"]
        city_lon = city["longitude"]
        nearest = min(
            remaining,
            key=lambda zone: _distance_sq(
                city_lat, city_lon, zone.center_lat, zone.center_lon
            ),
        )
        chosen.append(nearest.geohash)
        remaining.remove(nearest)

    return chosen


async def sync_analytics_target_flags(db: AsyncSession) -> list[str]:
    """
    Mark the canonical seven Norwegian city zones as analytics targets.

    This is idempotent and safe to run at startup or during a migration step.
    It clears any previous analytics flags first, then sets the seven nearest
    monitored zones to the predefined city coordinates.
    """
    result = await db.execute(select(MonitoredZone))
    zones = result.scalars().all()
    if not zones:
        logger.info("No monitored zones found; analytics target sync skipped.")
        return []

    candidate_zones = [
        _CandidateZone(
            geohash=zone.geohash,
            center_lat=zone.center_lat,
            center_lon=zone.center_lon,
        )
        for zone in zones
    ]
    chosen_geohashes = _pick_analytics_zones(candidate_zones)

    await db.execute(update(MonitoredZone).values(is_analytics_target=False))
    if chosen_geohashes:
        await db.execute(
            update(MonitoredZone)
            .where(MonitoredZone.geohash.in_(chosen_geohashes))
            .values(is_analytics_target=True)
        )
        await db.commit()
        logger.info(
            "Analytics target flags synced for %s monitored zones.",
            len(chosen_geohashes),
        )
    else:
        await db.commit()
        logger.info("No analytics target zones could be selected from monitored zones.")

    return chosen_geohashes
