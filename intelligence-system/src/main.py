"""Intelligence system worker: orchestrates risk calculations and pub/sub messaging.

Manages three concurrent tasks:
  1. Hourly scheduled risk calculations for all monitored zones
  2. Instant (ad-hoc) risk requests from the backend via Redis queue
  3. Event publication to Redis for dashboard and subscription updates

The system listens on Redis for frontend subscription requests and location
queries, publishing results back in real-time. All calculations are delegated
to the zone processor which handles MET API calls and risk model logic.
"""

import asyncio
import datetime
import json
import logging

import redis.asyncio as redis

from config import settings
from db.database import (
    create_db_and_tables,
    get_latest_readings,
    get_monitored_zones,
    get_zone_by_geohash,
    seed_initial_zones,
)
from services.zone_processor import process_zone

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntelligenceSystem")

# Redis Client
redis_client = redis.from_url(settings.REDIS_URL)


async def job() -> None:
    """Fetch weather data and calculate fire risk for all monitored zones (hourly).

    Executes concurrency-limited requests to MET API for weather readings,
    processes each zone's data through risk calculation model, and saves
    results to database. Emits HOURLY_DATA_READY event via Redis when complete.

    Note: Uses Semaphore to limit concurrent API requests (configurable via
    MAX_CONCURRENT_FETCHES setting) to avoid overloading external APIs or
    exhausting database connection pool.
    """
    logger.info("Starting fetch cycle...")

    monitored_zones = await get_monitored_zones()
    logger.info(f"Found {len(monitored_zones)} zones to monitor.")

    # Limit concurrency to avoid overloading MET API or DB connection pool
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_FETCHES)

    # Create tasks for all zones
    tasks = [process_zone(zone, semaphore) for zone in monitored_zones]

    # Run tasks concurrently
    await asyncio.gather(*tasks)

    logger.info("Fetch cycle completed.")

    # --- Debug Function Call ---
    # Fetch and print the latest reading for a sample zone
    if monitored_zones:
        sample_geohash = monitored_zones[0].geohash
        latest_data = await get_latest_readings(sample_geohash)
        logger.info(f"DEBUG - Latest data for {sample_geohash}: {latest_data}")

    # Publish event to Redis
    event_payload = {
        "event": "HOURLY_DATA_READY",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    await redis_client.publish("fireguard_events", json.dumps(event_payload))
    logger.info("Published HOURLY_DATA_READY event to fireguard_events")


async def process_instant_queue() -> None:
    """Listen for and process instant (ad-hoc) risk calculation requests from backend.

    Runs as long-lived coroutine that blocks on Redis (intelligence_tasks list),
    processing high-priority requests for specific locations. Each request includes
    a geohash/location_id; the worker fetches zone details, calculates risk,
    and publishes result back to Redis channel for the backend to stream to clients.

    Errors (missing zones, API failures) are logged and processing continues.
    Implements 5-second backoff on failure to avoid tight error loops.
    """
    logger.info("Instant Queue Processor Started.")
    while True:
        try:
            # Block until a message is added to 'intelligence_tasks'
            result = await redis_client.brpop("intelligence_tasks", timeout=0)
            if result:
                _, message = result
                task = json.loads(message)
                # Support both geohash (from backend) and location_id
                loc_id = task.get("geohash") or task.get("location_id")

                if not loc_id:
                    logger.warning("Received task without geohash or location_id")
                    continue

                logger.info(f"Instant task received for location: {loc_id}")

                # 1. Fetch zone details from DB
                zone = await get_zone_by_geohash(loc_id)
                if not zone:
                    logger.error(f"Zone {loc_id} not found in database.")
                    continue

                # 2. Process the zone
                risk_data = await process_zone(zone)

                if risk_data:
                    # 3. Publish the result back to Redis so the Backend can stream it
                    channel_name = f"location_updates:{loc_id}"
                    await redis_client.set(
                        f"location_updates:last:{loc_id}",
                        json.dumps(risk_data),
                        ex=3600,
                    )
                    await redis_client.publish(channel_name, json.dumps(risk_data))
                    logger.info(f"Published update to {channel_name}")

        except Exception as e:
            logger.error(f"Queue Error: {e}", exc_info=True)
            await asyncio.sleep(5)


async def process_scheduled_locations() -> None:
    """Run hourly background polling loop for all monitored zones.

    Repeatedly calls job() on a fixed interval (FETCH_INTERVAL_SECONDS) to
    ensure all zones receive regular weather updates and risk calculations.
    Implements 60-second error backoff if job() fails, then resumes normal
    schedule.

    This task forms the core of the intelligence system, keeping historical
    data fresh for both dashboard display and alerting logic.
    """
    logger.info("Scheduled Locations Processor Started.")
    while True:
        try:
            await job()
            logger.info(
                "Sleeping for %s seconds...",
                settings.FETCH_INTERVAL_SECONDS,
            )
            await asyncio.sleep(settings.FETCH_INTERVAL_SECONDS)
        except Exception as e:
            logger.error(f"Scheduled Task Error: {e}", exc_info=True)
            await asyncio.sleep(60)


async def main() -> None:
    """Initialize database and start concurrent worker task group.

    Seeds initial monitored zones (if empty) and spawns two long-lived tasks:
    - process_instant_queue(): Handles on-demand risk calculations
    - process_scheduled_locations(): Runs hourly bulk risk refresh cycle

    Both tasks run concurrently, coordinating via Redis messaging and shared
    database. Worker continues indefinitely until process is terminated.
    """
    logger.info("Intelligence System Worker Starting...")

    # Create DB tables and seed with initial zones
    await create_db_and_tables()
    await seed_initial_zones()

    # Run instant queue and scheduled tasks concurrently
    await asyncio.gather(process_instant_queue(), process_scheduled_locations())


if __name__ == "__main__":
    asyncio.run(main())
