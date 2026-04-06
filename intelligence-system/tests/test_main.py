import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from db.database import MonitoredZone
from main import job, process_instant_queue


@pytest.mark.asyncio
async def test_job_cycle(mock_db_session):
    """Verify the full job cycle: fetch -> calculate -> save."""

    # Mock the monitored zones
    mock_zone = MonitoredZone(
        geohash="u4p9x", center_lat=60.39, center_lon=5.32, name="Test Zone"
    )

    # Mock the MET API response
    mock_met_data = {
        "properties": {
            "timeseries": [
                {
                    "time": "2023-10-27T10:00:00Z",
                    "data": {
                        "instant": {
                            "details": {
                                "air_temperature": 10,
                                "relative_humidity": 50,
                                "wind_speed": 5,
                            }
                        }
                    },
                }
            ]
        },
        "type": "Feature",
    }

    # Mock the risk calculation result
    mock_risk_result = {"ttf": 5.5, "timestamp": "2023-10-27T10:00:00Z"}

    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock()

    # We patch AsyncSessionLocal in 'database' so that save_weather_data uses our mock
    # session. We also patch get_monitored_zones to avoid a DB query for zones.
    with (
        patch("db.database.AsyncSessionLocal", return_value=mock_db_session),
        patch("main.get_monitored_zones", return_value=[mock_zone]),
        patch("services.zone_processor.fetch_weather", return_value=mock_met_data),
        patch("services.zone_processor.calculate_risk", return_value=mock_risk_result),
        patch("main.redis_client", mock_redis),
    ):
        await job()

        # Verify that data was added to the session
        # We expect 2 additions: 1 for weather data, 1 for risk data
        assert mock_db_session.add.call_count == 2

        # Verify commit was called
        assert mock_db_session.commit.called

        # Verify redis publish was called
        assert mock_redis.publish.called


@pytest.mark.asyncio
async def test_process_instant_queue_success():
    """Verify that process_instant_queue correctly processes a task from Redis."""
    mock_zone = MonitoredZone(
        geohash="u4p9x", center_lat=60.39, center_lon=5.32, name="Test Zone"
    )
    task_message = json.dumps({"location_id": "u4p9x"})
    risk_data = {"location_id": "u4p9x", "risk_category": "High", "risk_score": 75.0}

    # Mock Redis client
    mock_redis = AsyncMock()
    # brpop returns (queue_name, message)
    mock_redis.brpop.side_effect = [
        ("intelligence_tasks", task_message),
        asyncio.CancelledError(),
    ]
    mock_redis.publish = AsyncMock()

    with (
        patch("main.redis_client", mock_redis),
        patch("main.get_zone_by_geohash", return_value=mock_zone),
        patch("main.process_zone", return_value=risk_data),
    ):
        with pytest.raises(asyncio.CancelledError):
            await process_instant_queue()

        # Verify Redis interactions
        mock_redis.brpop.assert_called()
        mock_redis.publish.assert_called_with(
            "location_updates:u4p9x", json.dumps(risk_data)
        )
