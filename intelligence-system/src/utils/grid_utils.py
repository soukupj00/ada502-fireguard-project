"""Grid/geohash helpers for seeding and analytics-target zone selection."""

from dataclasses import dataclass
from typing import Iterable, List, Tuple

import pygeohash as pgh

from utils.constants import ANALYTICS_CITIES


@dataclass(frozen=True)
class _CandidateZone:
    geohash: str
    center_lat: float
    center_lon: float


def get_geohash(lat: float, lon: float, precision: int = 5) -> str:
    """
    Converts latitude and longitude to a geohash string.

    Args:
        lat: Latitude.
        lon: Longitude.
        precision: Length of the geohash string.
                   3 chars ~= 156km x 156km (Coarse Regional Tier)
                   4 chars ~= 39km x 19km (Finer Regional Tier)
                   5 chars ~= 4.9km x 4.9km (Precise Tier for User Alerts)

    Returns:
        The geohash string.
    """
    return pgh.encode(lat, lon, precision=precision)


def get_geohash_center(geohash: str) -> Tuple[float, float]:
    """
    Decodes a geohash string to its center latitude and longitude.

    Args:
        geohash: The geohash string.

    Returns:
        A tuple of (latitude, longitude).
    """
    lat, lon = pgh.decode(geohash)
    # pygeohash returns strings or floats depending on version, ensure float
    return float(lat), float(lon)


def _distance_sq(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return squared Euclidean distance between two latitude/longitude points."""
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


def mark_analytics_targets(zones: List[dict]) -> List[dict]:
    """Mark a subset of zones as analytics targets based on nearest city mapping."""
    if not zones:
        return zones

    candidate_zones = [
        _CandidateZone(
            geohash=zone["geohash"],
            center_lat=zone["center_lat"],
            center_lon=zone["center_lon"],
        )
        for zone in zones
    ]
    chosen_geohashes = set(_pick_analytics_zones(candidate_zones))

    for zone in zones:
        zone["is_analytics_target"] = zone["geohash"] in chosen_geohashes

    return zones


def generate_initial_zones() -> List[dict]:
    """
    Generates a list of 'Tier 1' (Regional) zones covering
    the entire bounding box of Norway.
    These zones use coarser geohash precision (3 characters) for a broader overview,
    suitable for a national map.

    Returns:
        A list of dictionaries representing zones.
    """
    zones = []
    seen_hashes = set()

    # Approximate bounding box for Norway
    lat_min, lat_max = 57.9, 71.2
    lon_min, lon_max = 4.6, 31.1

    # Step size in degrees.
    # We use a step size smaller than the dimensions of a 3-char geohash
    # to ensure we don't skip any blocks.
    # 3-char geohash is approx 1.4 deg lat x 2.8 deg lon at 60N.
    # Using 0.5 and 1.0 ensures full coverage (oversampling is handled by deduplication)
    lat_step = 0.5
    lon_step = 1.0

    current_lat = lat_min
    while current_lat <= lat_max:
        current_lon = lon_min
        while current_lon <= lon_max:
            # Generate a Tier 1 (Regional) geohash (precision 3)
            gh = get_geohash(current_lat, current_lon, precision=3)

            if gh not in seen_hashes:
                lat, lon = get_geohash_center(gh)
                zones.append(
                    {
                        "geohash": gh,
                        "center_lat": lat,
                        "center_lon": lon,
                        "is_regional": True,
                        "name": f"Regional Zone {gh}",
                        "is_analytics_target": False,
                    }
                )
                seen_hashes.add(gh)

            current_lon += lon_step
        current_lat += lat_step

    return mark_analytics_targets(zones)
