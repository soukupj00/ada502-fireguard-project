import asyncio
import logging
import random
from typing import Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.db.models import CurrentFireRisk, MonitoredZone, WeatherDataReading
from app.services.thingspeak_service import thingspeak_client

logger = logging.getLogger(__name__)

# Store last sent values to detect if they changed
_last_sent_values: Dict[str, Optional[float]] = {}


def _add_random_variation(value: Optional[float]) -> Optional[float]:
    """
    If value exists, randomly increase or decrease it by 1.
    This simulates data changes for testing graph visualization.
    """
    if value is None:
        return None
    # Randomly add or subtract 1
    variation = random.choice([-1, 1])
    return max(0, value + variation)  # Ensure non-negative


def _extract_weather_data(
    weather_data: Optional[dict],
) -> tuple[Optional[float], Optional[float]]:
    """Extract temperature and humidity from weather data."""
    temp = None
    rh = None
    try:
        if weather_data:
            ts = weather_data.get("properties", {}).get("timeseries", [])
            if ts:
                details = ts[0]["data"]["instant"]["details"]
                temp = details.get("air_temperature")
                rh = details.get("relative_humidity")
    except Exception:
        pass
    return temp, rh


async def _process_zone_data(
    db: AsyncSession, zone, field_index: int, data_points: dict
) -> int:
    """Process a single zone's data and add to data_points."""
    # Current risk for this geohash
    risk_q = select(CurrentFireRisk).where(CurrentFireRisk.geohash == zone.geohash)
    risk_res = await db.execute(risk_q)
    risk = risk_res.scalars().first()

    # Latest weather reading for this zone
    weather_q = select(WeatherDataReading).where(
        WeatherDataReading.location_name == zone.geohash
    )
    weather_res = await db.execute(weather_q)
    latest_weather = weather_res.scalars().first()

    # Extract weather metrics
    temp, rh = _extract_weather_data(latest_weather.data if latest_weather else None)

    # Apply random variation if values haven't changed
    temp_key = f"temp_{zone.geohash}"
    rh_key = f"rh_{zone.geohash}"
    risk_key = f"risk_{zone.geohash}"

    if temp == _last_sent_values.get(temp_key):
        temp = _add_random_variation(temp)
    if rh == _last_sent_values.get(rh_key):
        rh = _add_random_variation(rh)

    risk_score = getattr(risk, "risk_score", None)
    if risk_score == _last_sent_values.get(risk_key):
        risk_score = _add_random_variation(risk_score)

    # Store values
    _last_sent_values[temp_key] = temp
    _last_sent_values[rh_key] = rh
    _last_sent_values[risk_key] = risk_score

    # Add to data points
    data_points[f"field{field_index}"] = temp
    field_index += 1
    data_points[f"field{field_index}"] = rh
    field_index += 1
    data_points[f"field{field_index}"] = risk_score
    field_index += 1

    return field_index


async def _thingspeak_test_push_cycle(db: AsyncSession) -> None:
    """
    Single push cycle: fetch analytics target zones and push to ThingSpeak.

    Includes random value variation if values haven't changed from last push.
    """
    try:
        # 1. Get analytics target zones from DB
        zones_query = select(MonitoredZone).where(MonitoredZone.is_analytics_target)
        zones_result = await db.execute(zones_query)
        zones = zones_result.scalars().all()

        if not zones:
            logger.debug("ThingSpeak Test: No analytics target zones found.")
            return

        # 2. Process each zone
        data_points: dict = {}
        field_index = 1

        for zone in zones:
            field_index = await _process_zone_data(db, zone, field_index, data_points)

        # 3. Calculate and add national average (with variation if unchanged)
        try:
            avg_query = select(func.avg(CurrentFireRisk.risk_score))
            avg_result = await db.execute(avg_query)
            national_average = avg_result.scalar_one_or_none()

            avg_key = "national_average"
            if national_average == _last_sent_values.get(avg_key):
                national_average = _add_random_variation(national_average)
            _last_sent_values[avg_key] = national_average

            if national_average is not None and field_index <= 8:
                data_points[f"field{field_index}"] = national_average
        except Exception:
            pass

        if data_points:
            logger.info(
                f"ThingSpeak Test: Pushing {len(data_points)} field(s) to ThingSpeak..."
            )
            res = thingspeak_client.push_data(data_points)
            if asyncio.iscoroutine(res):
                await res
        else:
            logger.debug("ThingSpeak Test: No data found to push.")

    except Exception as e:
        logger.error(f"ThingSpeak Test: Error in push cycle: {e}", exc_info=True)


async def thingspeak_test_push_task() -> None:
    """
    Testing background task that pushes analytics data to ThingSpeak
    every minute for predefined analytics target locations.

    Includes random value variation to simulate data changes for testing
    graph visualization.

    Can be controlled via THINGSPEAK_TEST_MODE environment variable.
    """
    logger.info(
        "ThingSpeak Test Task: Starting 1-minute interval push to analytics channel..."
    )

    try:
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    await _thingspeak_test_push_cycle(db)
            except Exception as e:
                logger.error(
                    f"ThingSpeak Test Task: Error in push cycle: {e}", exc_info=True
                )

            # Wait 60 seconds before next push
            await asyncio.sleep(60)

    except asyncio.CancelledError:
        logger.info("ThingSpeak Test Task: Cancelled.")
        raise
    except Exception as e:
        logger.error(f"ThingSpeak Test Task: Unexpected error: {e}", exc_info=True)
        raise
