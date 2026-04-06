import asyncio
from unittest.mock import patch

import pytest

from db.database import MonitoredZone
from services.zone_processor import process_zone


@pytest.mark.asyncio
async def test_process_zone_success(mock_db_session):
    """Test successful zone processing."""
    mock_zone = MonitoredZone(
        geohash="u4p9x", center_lat=60.39, center_lon=5.32, name="Test Zone"
    )

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

    mock_risk_result = {"ttf": 5.5, "timestamp": "2023-10-27T10:00:00Z"}

    with (
        patch(
            "services.zone_processor.fetch_weather", return_value=mock_met_data
        ) as mock_fetch,
        patch(
            "services.zone_processor.calculate_risk", return_value=mock_risk_result
        ) as mock_calc,
        patch(
            "services.zone_processor.save_weather_data", return_value=None
        ) as mock_save_weather,
        patch(
            "services.zone_processor.save_risk_data", return_value=None
        ) as mock_save_risk,
    ):
        result = await process_zone(mock_zone)

        assert result is not None
        assert result["location_id"] == "u4p9x"
        assert result["ttf"] == 5.5
        assert "risk_category" in result
        assert "risk_score" in result

        mock_fetch.assert_called_once_with(60.39, 5.32)
        mock_calc.assert_called_once_with(mock_met_data)
        mock_save_weather.assert_called_once()
        mock_save_risk.assert_called_once()


@pytest.mark.asyncio
async def test_process_zone_fetch_failure():
    """Test zone processing when weather fetch fails."""
    mock_zone = MonitoredZone(
        geohash="u4p9x", center_lat=60.39, center_lon=5.32, name="Test Zone"
    )

    with patch("services.zone_processor.fetch_weather", return_value=None):
        result = await process_zone(mock_zone)
        assert result is None


@pytest.mark.asyncio
async def test_process_zone_risk_calc_failure():
    """Test zone processing when risk calculation fails."""
    mock_zone = MonitoredZone(
        geohash="u4p9x", center_lat=60.39, center_lon=5.32, name="Test Zone"
    )

    mock_met_data = {"some": "data"}

    with (
        patch("services.zone_processor.fetch_weather", return_value=mock_met_data),
        patch("services.zone_processor.calculate_risk", return_value=None),
        patch("services.zone_processor.save_weather_data", return_value=None),
    ):
        result = await process_zone(mock_zone)
        assert result is None


@pytest.mark.asyncio
async def test_process_zone_with_semaphore():
    """Test zone processing respects semaphore."""
    mock_zone = MonitoredZone(
        geohash="u4p9x", center_lat=60.39, center_lon=5.32, name="Test Zone"
    )
    semaphore = asyncio.Semaphore(1)

    mock_risk_result = {"ttf": 5.5, "timestamp": "2023-10-27T10:00:00Z"}

    with (
        patch("services.zone_processor.fetch_weather", return_value={"data": "ok"}),
        patch("services.zone_processor.calculate_risk", return_value=mock_risk_result),
        patch("services.zone_processor.save_weather_data", return_value=None),
        patch("services.zone_processor.save_risk_data", return_value=None),
    ):
        # We just want to ensure it runs without error when semaphore is passed
        result = await process_zone(mock_zone, semaphore=semaphore)
        assert result is not None
