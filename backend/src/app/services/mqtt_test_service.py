import asyncio
import logging

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import CurrentFireRisk, UserSubscription
from app.services.mqtt_service import mqtt_client

logger = logging.getLogger(__name__)


async def _mqtt_test_push_cycle():
    """
    Single push cycle: fetch subscribed geohashes and publish their risk data.
    """
    async with AsyncSessionLocal() as db:
        # 1. Get all unique geohashes that users are subscribed to
        sub_query = select(UserSubscription.geohash).distinct()
        sub_result = await db.execute(sub_query)
        subscribed_geohashes = sub_result.scalars().all()

        if not subscribed_geohashes:
            logger.debug("MQTT Test: No active user subscriptions found.")
            return

        # 2. Get all current fire risk data for these geohashes
        risk_query = select(CurrentFireRisk).where(
            CurrentFireRisk.geohash.in_(subscribed_geohashes)
        )
        risk_result = await db.execute(risk_query)
        risks = risk_result.scalars().all()

        if not risks:
            logger.debug("MQTT Test: No current fire risk data found.")
            return

        # 3. Publish all risks to MQTT
        logger.info(f"MQTT Test: Publishing {len(risks)} risk updates...")
        for risk in risks:
            mqtt_client.publish_alert(
                geohash=risk.geohash,
                risk_level=risk.risk_category or "Unknown",
                risk_score=risk.risk_score or 0.0,
            )


async def mqtt_test_push_task():
    """
    Testing background task that pushes all current fire risk data to MQTT
    for all user subscriptions every 30 seconds.

    This is used for testing MQTT connectivity and frontend reception.
    Can be controlled via MQTT_TEST_MODE environment variable.
    """
    logger.info(
        "MQTT Test Task: Starting 30-second interval push of all user subscriptions..."
    )

    try:
        while True:
            try:
                await _mqtt_test_push_cycle()
            except Exception as e:
                logger.error(f"MQTT Test Task: Error in push cycle: {e}", exc_info=True)

            # Wait 30 seconds before next push
            await asyncio.sleep(30)

    except asyncio.CancelledError:
        logger.info("MQTT Test Task: Cancelled.")
        raise
    except Exception as e:
        logger.error(f"MQTT Test Task: Unexpected error: {e}", exc_info=True)
        raise
