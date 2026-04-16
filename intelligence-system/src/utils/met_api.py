"""MET.no weather API client helpers used by the intelligence worker."""

import logging
from typing import Any

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MET.no Locationforecast 2.0 Endpoint
MET_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

# MANDATORY: Identify yourself to MET.no
HEADERS = {
    "User-Agent": "FireGuard/1.0 (student.email@uib.no)",
    "Content-Type": "application/json",
}


async def fetch_weather(lat: float, lon: float) -> Any | None:
    """
    Asynchronously fetches weather data for a given latitude and longitude from the
    MET.no API.

    Args:
        lat: The latitude of the location.
        lon: The longitude of the location.

    Returns:
        A dictionary containing the weather data, or None if an error occurs.
    """
    params = {"lat": lat, "lon": lon}

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.get(MET_URL, headers=HEADERS, params=params)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch MET data: {e}")
            return None
