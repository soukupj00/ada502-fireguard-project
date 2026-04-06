import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import httpx

from config import settings

logger = logging.getLogger(__name__)


class ThingSpeakService:
    def __init__(self):
        self.api_key = settings.THINGSPEAK_WRITE_API_KEY
        self.base_url = "https://api.thingspeak.com/update"
        # Backfill can use the bulk API when channel id is available.
        self.channel_id = settings.THINGSPEAK_CHANNEL_ID or os.getenv(
            "VITE_THINGSPEAK_CHANNEL_ID"
        )

    @staticmethod
    def _format_thingspeak_timestamp(ts: datetime) -> str:
        # ThingSpeak accepts ISO8601. Normalize to UTC and include trailing Z.
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat()

    async def push_data(
        self, data_points: Dict[str, Any], created_at: datetime | None = None
    ) -> bool:
        """
        Pushes an arbitrary dictionary of data to ThingSpeak fields.
        Keys should be field names (e.g. 'field1', 'field2').
        Values should be the data points.

        Example: data_points = {'field1': 25.5, 'field2': 60, 'field3': 85.0}
        """
        if not self.api_key:
            logger.warning("ThingSpeak API Key not found. Cannot push analytics data.")
            return False

        params = {
            "api_key": self.api_key,
        }

        if created_at is not None:
            params["created_at"] = self._format_thingspeak_timestamp(created_at)

        # Merge the api_key with the data points
        for key, value in data_points.items():
            if value is not None:
                params[key] = str(value)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, params=params)
                response.raise_for_status()  # Raise an exception for bad status codes

                # ThingSpeak returns '0' if the update failed (e.g. rate limit hit)
                # or a channel entry ID if it succeeded.
                if response.text.strip() == "0":
                    logger.error(
                        "ThingSpeak update failed. Rate limit may have been exceeded "
                        "(updates allowed every 15 seconds)."
                    )
                    return False

                logger.info(
                    f"Successfully pushed data to ThingSpeak. Entry ID: {response.text}"
                )
                return True

        except httpx.HTTPStatusError as exc:
            logger.error(f"HTTP error while pushing to ThingSpeak: {exc}")
        except Exception as exc:
            logger.error(
                f"An unexpected error occurred while pushing to ThingSpeak: {exc}"
            )

        return False

    async def push_bulk_data(self, updates: list[Dict[str, Any]]) -> bool:
        """
        Push multiple timestamped entries in one request.
        Each update item may include created_at and field1..field8.
        """
        if not self.api_key:
            logger.warning("ThingSpeak API Key not found. Cannot push analytics data.")
            return False
        if not self.channel_id:
            logger.warning(
                "ThingSpeak channel id not configured. "
                "Cannot perform bulk backfill push."
            )
            return False
        if not updates:
            return True

        payload_updates: list[Dict[str, Any]] = []
        for item in updates:
            converted: Dict[str, Any] = {}
            for key, value in item.items():
                if value is None:
                    continue
                if key == "created_at" and isinstance(value, datetime):
                    converted[key] = self._format_thingspeak_timestamp(value)
                else:
                    converted[key] = str(value)
            if converted:
                payload_updates.append(converted)

        if not payload_updates:
            return True

        payload = {
            "write_api_key": self.api_key,
            "updates": payload_updates,
        }

        bulk_url = (
            f"https://api.thingspeak.com/channels/{self.channel_id}/bulk_update.json"
        )
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(bulk_url, json=payload)
                response.raise_for_status()
                logger.info(
                    "Successfully pushed %s historical updates to ThingSpeak.",
                    len(payload_updates),
                )
                return True
        except httpx.HTTPStatusError as exc:
            logger.error("HTTP error while pushing ThingSpeak bulk data: %s", exc)
        except Exception as exc:
            logger.error(
                "An unexpected error occurred while pushing ThingSpeak bulk data: %s",
                exc,
            )
        return False


# Singleton instance
thingspeak_client = ThingSpeakService()
