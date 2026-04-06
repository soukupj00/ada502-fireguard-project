import asyncio
import json
import logging

from app.services.event_processor_service import process_hourly_data_ready_event
from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)


def _log_task_exception(task: asyncio.Task) -> None:
    try:
        exc = task.exception()
    except asyncio.CancelledError:
        return
    if exc:
        logger.error("Hourly task failed: %s", exc)


def _handle_fireguard_message(message: dict) -> None:
    if message["type"] != "message":
        return

    try:
        data = json.loads(message["data"].decode("utf-8"))
        event_type = data.get("event")

        if event_type == "HOURLY_DATA_READY":
            logger.info(f"Received event: {event_type} at {data.get('timestamp')}")
            hourly_task = asyncio.create_task(process_hourly_data_ready_event())
            hourly_task.add_done_callback(_log_task_exception)
        else:
            logger.debug(f"Received unknown event type: {event_type}")

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from Redis message.")
    except Exception as e:
        logger.error(f"Error processing Redis message: {e}")


async def redis_listener_task():
    """
    Background task that listens to the Redis 'fireguard_events' channel.
    When a HOURLY_DATA_READY event is received, it triggers the orchestration logic
    for MQTT alerts and ThingSpeak analytics.
    """
    logger.info("Starting Redis event listener task...")
    redis_client = await get_redis_client()
    pubsub = redis_client.pubsub()

    await pubsub.subscribe("fireguard_events")
    logger.info("Subscribed to 'fireguard_events' channel.")

    try:
        async for message in pubsub.listen():
            _handle_fireguard_message(message)
    finally:
        await pubsub.unsubscribe("fireguard_events")
        logger.info("Unsubscribed from 'fireguard_events' channel.")
