from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.analytics_targets import _pick_analytics_zones, sync_analytics_target_flags
from app.db.models import MonitoredZone


class _FakeScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


@pytest.mark.asyncio
async def test_sync_analytics_target_flags_marks_nearest_zones_true():
    oslo_like = MonitoredZone(geohash="oslo-gh", center_lat=59.9, center_lon=10.7)
    bergen_like = MonitoredZone(geohash="bergen-gh", center_lat=60.4, center_lon=5.3)

    db = AsyncMock()
    db.execute.side_effect = [
        _FakeScalarResult([oslo_like, bergen_like]),
        MagicMock(),
        MagicMock(),
    ]
    db.commit = AsyncMock()

    chosen = await sync_analytics_target_flags(db)

    assert chosen == ["oslo-gh", "bergen-gh"]
    assert db.execute.call_count == 3
    db.commit.assert_awaited_once()


def test_pick_analytics_zones_is_deterministic_and_city_ordered():
    zones = [
        type("Zone", (), {"geohash": "a", "center_lat": 59.91, "center_lon": 10.75})(),
        type("Zone", (), {"geohash": "b", "center_lat": 60.39, "center_lon": 5.32})(),
    ]

    assert _pick_analytics_zones(zones) == ["a", "b"]
