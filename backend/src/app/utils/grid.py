from typing import Tuple

import pygeohash as pgh


def get_geohash(lat: float, lon: float, precision: int = 5) -> str:
    """
    Convert latitude/longitude coordinates into a geohash.

    Args:
        lat: Latitude.
        lon: Longitude.
        precision: Length of the geohash string.
            - 3 chars ~= 156 km x 156 km (coarse regional tier)
            - 4 chars ~= 39 km x 19 km (finer regional tier)
            - 5 chars ~= 4.9 km x 4.9 km (precise tier for user alerts)

    Returns:
        The geohash string.
    """
    return pgh.encode(lat, lon, precision=precision)


def get_geohash_center(geohash: str) -> Tuple[float, float]:
    """
    Decode a geohash into its center latitude/longitude.

    Args:
        geohash: The geohash string.

    Returns:
        A tuple of (latitude, longitude).
    """
    lat, lon = pgh.decode(geohash)
    # Some pygeohash versions return strings; normalize output to floats.
    return float(lat), float(lon)
