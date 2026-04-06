from utils.grid_utils import generate_initial_zones, get_geohash, get_geohash_center


def test_get_geohash_precision():
    """Verify geohash precision logic."""
    lat, lon = 60.3913, 5.3221  # Bergen

    # Precision 5 (User Tier)
    gh5 = get_geohash(lat, lon, precision=5)
    assert len(gh5) == 5
    assert gh5 == "u4ez9"

    # Precision 4 (Regional Tier)
    gh4 = get_geohash(lat, lon, precision=4)
    assert len(gh4) == 4
    assert gh4 == "u4ez"

    # Precision 3 (Coarse Regional Tier)
    gh3 = get_geohash(lat, lon, precision=3)
    assert len(gh3) == 3
    assert gh3 == "u4e"


def test_get_geohash_center():
    """Verify decoding logic."""
    geohash = "u4ez9"
    lat, lon = get_geohash_center(geohash)

    # Bergen is roughly 60.39, 5.32
    assert 60.3 < lat < 60.5
    assert 5.2 < lon < 5.4


def test_generate_initial_zones_coverage():
    """Verify that we generate a reasonable number of zones covering Norway."""
    zones = generate_initial_zones()

    # With precision 3, we expect roughly 80-100 zones
    assert len(zones) > 50
    assert len(zones) < 200

    # Check the structure of a zone
    first_zone = zones[0]
    assert "geohash" in first_zone
    assert len(first_zone["geohash"]) == 3
    assert first_zone["is_regional"] is True
    assert "center_lat" in first_zone
    assert "center_lon" in first_zone


def test_generate_initial_zones_marks_analytics_targets():
    """Verify that the canonical analytics targets are flagged in the seed set."""
    zones = generate_initial_zones()
    analytics_targets = [zone for zone in zones if zone["is_analytics_target"]]

    assert len(analytics_targets) == 7
    assert all(len(zone["geohash"]) == 3 for zone in analytics_targets)
