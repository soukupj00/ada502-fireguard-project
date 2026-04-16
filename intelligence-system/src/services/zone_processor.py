"""Zone processing pipeline for weather fetch, risk calculation, and persistence."""

import asyncio
import logging
from typing import Any, Dict

from db.database import save_risk_data, save_weather_data
from utils.fire_risk_service import calculate_risk, calculate_risk_score
from utils.met_api import fetch_weather

logger = logging.getLogger(__name__)


async def process_zone(
    zone: Any, semaphore: asyncio.Semaphore | None = None
) -> Dict[str, Any] | None:
    """
    Fetch weather, calculate risk, and persist readings for one zone.

    If a semaphore is provided, processing is executed within that concurrency
    guard to avoid overloading external APIs and the database.

    Returns a lightweight risk payload for Redis publishing when successful,
    otherwise ``None``.
    """
    if semaphore:
        async with semaphore:
            return await _do_process_zone(zone)
    else:
        return await _do_process_zone(zone)


async def _do_process_zone(zone: Any) -> Dict[str, Any] | None:
    """Run the zone processing flow without a semaphore wrapper."""
    logger.info(f"Processing zone: {zone.name} ({zone.geohash})")

    # 1. Fetch weather for the center of the zone
    met_data = await fetch_weather(zone.center_lat, zone.center_lon)

    if not met_data:
        logger.warning(f"Skipping zone {zone.geohash} due to fetch error.")
        return None

    # Save raw weather data to the database
    await save_weather_data(
        location_name=zone.geohash,
        lat=zone.center_lat,
        lon=zone.center_lon,
        weather_json=met_data,
    )

    # 2. Compute Risk
    risk_result = calculate_risk(met_data)

    if risk_result:
        logger.info(f"Zone: {zone.geohash}, TTF: {risk_result['ttf']}")

        # 3. Save risk result to DB
        await save_risk_data(
            location_name=zone.geohash,
            lat=zone.center_lat,
            lon=zone.center_lon,
            risk_result=risk_result,
        )

        # Prepare risk data for Redis/Streaming
        risk_score, risk_category = calculate_risk_score(risk_result["ttf"])
        return {
            "location_id": zone.geohash,
            "risk_category": risk_category,  # Changed from risk_level to risk_category
            "risk_score": risk_score,
            "ttf": risk_result["ttf"],
            "timestamp": risk_result["timestamp"].isoformat()
            if hasattr(risk_result["timestamp"], "isoformat")
            else risk_result["timestamp"],
        }
    else:
        logger.warning(f"Risk calculation failed for zone {zone.geohash}")
        return None
