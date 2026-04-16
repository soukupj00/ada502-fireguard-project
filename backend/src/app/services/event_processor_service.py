import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.db.models import (
    CurrentFireRisk,
    FireRiskReading,
    MonitoredZone,
    UserSubscription,
)
from app.services.mqtt_service import mqtt_client
from app.services.thingspeak_service import thingspeak_client
from app.utils.constants import (
    THINGSPEAK_CITY_COORDS,
    THINGSPEAK_CITY_FIELD_ORDER,
    THINGSPEAK_NATIONAL_AVERAGE_FIELD,
)

logger = logging.getLogger(__name__)


async def process_hourly_data_ready_event():
    """
    Main orchestration function triggered by the HOURLY_DATA_READY Redis event.
    """
    logger.info("Processing HOURLY_DATA_READY event...")

    async with AsyncSessionLocal() as db:
        await process_mqtt_alerts(db)
        await process_thingspeak_analytics(db)

    logger.info("Finished processing HOURLY_DATA_READY event.")


async def process_mqtt_alerts(db: AsyncSession):
    """
    Finds geohashes with active user subscriptions that are in High or Extreme risk,
    and publishes MQTT alerts for them.
    """
    try:
        # 1. Get all unique geohashes that users are subscribed to
        sub_query = select(UserSubscription.geohash).distinct()
        sub_result = await db.execute(sub_query)
        subscribed_geohashes = sub_result.scalars().all()

        if not subscribed_geohashes:
            logger.info("No active user subscriptions found. Skipping MQTT alerts.")
            return

        # 2. Find which of these subscribed geohashes are in High/Extreme risk
        risk_query = select(CurrentFireRisk).where(
            CurrentFireRisk.geohash.in_(subscribed_geohashes),
            CurrentFireRisk.risk_category.in_(["High", "Extreme"]),
        )
        risk_result = await db.execute(risk_query)
        high_risk_zones = risk_result.scalars().all()

        if not high_risk_zones:
            logger.info("No subscribed zones are currently at High/Extreme risk.")
            return

        # 3. Publish alerts
        for risk in high_risk_zones:
            mqtt_client.publish_alert(
                geohash=risk.geohash,
                risk_level=risk.risk_category,
                risk_score=risk.risk_score,
            )

    except Exception as e:
        logger.error(f"Error processing MQTT alerts: {e}")


async def process_thingspeak_analytics(db: AsyncSession):
    """
    Pushes fire risk analytics with fixed ThingSpeak mapping:
    field1..field7 city risk_score, field8 national average.
    to a ThingSpeak channel.
    """
    try:
        city_geohashes = await _resolve_analytics_city_geohashes(db)
        if not city_geohashes:
            logger.warning("No analytics target zones found. Skipping ThingSpeak push.")
            return

        risk_query = select(CurrentFireRisk).where(
            CurrentFireRisk.geohash.in_(list(city_geohashes.values()))
        )
        risk_result = await db.execute(risk_query)
        risk_rows = risk_result.scalars().all()
        risk_map = {row.geohash: row.risk_score for row in risk_rows}

        city_scores = {
            city: risk_map.get(geohash) for city, geohash in city_geohashes.items()
        }

        avg_query = select(func.avg(CurrentFireRisk.risk_score))
        avg_result = await db.execute(avg_query)
        national_average = avg_result.scalar_one_or_none()

        payload = _build_thingspeak_payload(city_scores, national_average)
        if not payload:
            logger.warning("No analytics values found to push to ThingSpeak.")
            return

        res = thingspeak_client.push_data(payload)
        if asyncio.iscoroutine(res):
            await res

    except Exception:
        logger.exception("Error processing ThingSpeak analytics")


def _build_thingspeak_payload(
    city_scores: dict[str, float | None], national_average: float | None
) -> dict[str, float]:
    """Build a ThingSpeak field payload from city and national scores.

    The mapping uses fixed field ordering from
    ``THINGSPEAK_CITY_FIELD_ORDER`` and only includes values that are present.
    """
    payload: dict[str, float] = {}
    for index, city in enumerate(THINGSPEAK_CITY_FIELD_ORDER, start=1):
        score = city_scores.get(city)
        if score is not None:
            payload[f"field{index}"] = score
    if national_average is not None:
        payload[THINGSPEAK_NATIONAL_AVERAGE_FIELD] = national_average
    return payload


def _distance_sq(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return squared Euclidean distance between two lat/lon points."""
    return (lat1 - lat2) ** 2 + (lon1 - lon2) ** 2


async def _resolve_analytics_city_geohashes(db: AsyncSession) -> dict[str, str]:
    """
    Resolve fixed city names to analytics target geohashes.
    We map by nearest analytics-target zone center to each city coordinate.
    """
    zones_query = select(MonitoredZone).where(MonitoredZone.is_analytics_target)
    zones_result = await db.execute(zones_query)
    zones = zones_result.scalars().all()

    if not zones:
        # Fallback for deployments where analytics flags are not yet populated.
        regional_query = select(MonitoredZone).where(MonitoredZone.is_regional)
        regional_result = await db.execute(regional_query)
        zones = regional_result.scalars().all()
        if zones:
            logger.info(
                "No analytics-target zones found; falling back to "
                "regional zones for ThingSpeak mapping."
            )

    if not zones:
        all_query = select(MonitoredZone)
        all_result = await db.execute(all_query)
        zones = all_result.scalars().all()
        if zones:
            logger.info(
                "No regional zones found; falling back to "
                "all monitored zones for ThingSpeak mapping."
            )

    if not zones:
        return {}

    remaining = list(zones)
    mapping: dict[str, str] = {}
    for city in THINGSPEAK_CITY_FIELD_ORDER:
        city_coords = THINGSPEAK_CITY_COORDS.get(city)
        if not city_coords or not remaining:
            continue
        city_lat, city_lon = city_coords
        nearest = min(
            remaining,
            key=lambda z: _distance_sq(city_lat, city_lon, z.center_lat, z.center_lon),
        )
        mapping[city] = nearest.geohash
        remaining.remove(nearest)
    return mapping


def _to_hour_bucket(ts: datetime) -> datetime:
    """Normalize a timestamp to the UTC hour bucket used by analytics backfill."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ts = ts.astimezone(timezone.utc)
    return ts.replace(minute=0, second=0, microsecond=0)


async def backfill_thingspeak_last_24h(hours: int = 24) -> None:
    """
    Push historical hourly analytics for the last 24h so the ThingSpeak channel
    has immediate chart history after deployment/startup.
    """
    logger.info("Starting ThingSpeak backfill for the last %s hours...", hours)
    try:
        async with AsyncSessionLocal() as db:
            city_geohashes = await _resolve_analytics_city_geohashes(db)
            if not city_geohashes:
                logger.warning(
                    "ThingSpeak backfill skipped: no analytics target zones."
                )
                return

            now_utc = datetime.now(timezone.utc)
            window_start = now_utc - timedelta(hours=hours)

            history_query = select(
                FireRiskReading.location_name,
                FireRiskReading.risk_score,
                FireRiskReading.prediction_timestamp,
            ).where(
                FireRiskReading.location_name.in_(list(city_geohashes.values())),
                FireRiskReading.prediction_timestamp >= window_start,
                FireRiskReading.risk_score.is_not(None),
            )
            history_query = history_query.order_by(
                FireRiskReading.prediction_timestamp.asc()
            )
            history_rows = (await db.execute(history_query)).all()

            hour_col = func.date_trunc(
                "hour", FireRiskReading.prediction_timestamp
            ).label("hour_bucket")
            avg_query = select(hour_col, func.avg(FireRiskReading.risk_score)).where(
                FireRiskReading.prediction_timestamp >= window_start,
                FireRiskReading.risk_score.is_not(None),
            )
            avg_query = avg_query.group_by(hour_col).order_by(hour_col)
            avg_rows = (await db.execute(avg_query)).all()

            reverse_map = {geohash: city for city, geohash in city_geohashes.items()}
            updates_by_hour: dict[datetime, dict[str, float]] = {}

            for location_name, risk_score, prediction_timestamp in history_rows:
                city = reverse_map.get(location_name)
                if city is None or risk_score is None:
                    continue
                hour_bucket = _to_hour_bucket(prediction_timestamp)
                field_name = f"field{THINGSPEAK_CITY_FIELD_ORDER.index(city) + 1}"
                updates_by_hour.setdefault(hour_bucket, {})[field_name] = risk_score

            for hour_bucket, avg_score in avg_rows:
                if avg_score is None:
                    continue
                bucket_dt = _to_hour_bucket(hour_bucket)
                updates_by_hour.setdefault(bucket_dt, {})[
                    THINGSPEAK_NATIONAL_AVERAGE_FIELD
                ] = avg_score

            if not updates_by_hour:
                logger.info("ThingSpeak backfill found no data to push.")
                return

            updates = []
            for hour_bucket in sorted(updates_by_hour.keys()):
                item: dict[str, float | datetime] = {"created_at": hour_bucket}
                item.update(updates_by_hour[hour_bucket])
                if len(item) > 1:
                    updates.append(item)

            if not updates:
                logger.info("ThingSpeak backfill has no valid updates after filtering.")
                return

            bulk_result = thingspeak_client.push_bulk_data(updates)
            if asyncio.iscoroutine(bulk_result):
                await bulk_result
            logger.info(
                "ThingSpeak backfill completed with %s update(s).", len(updates)
            )
    except Exception:
        logger.exception("ThingSpeak backfill failed")
