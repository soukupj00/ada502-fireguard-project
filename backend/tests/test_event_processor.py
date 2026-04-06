from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models import (
    CurrentFireRisk,
    MonitoredZone,
)
from app.services.event_processor_service import (
    process_mqtt_alerts,
    process_thingspeak_analytics,
)


@pytest.fixture
def mock_db_session():
    # Properly mock an AsyncSession and its execute -> scalars -> all/first chain
    session = AsyncMock()
    return session


@pytest.mark.asyncio
@patch("app.services.event_processor_service.mqtt_client")
async def test_process_mqtt_alerts_with_high_risk(mock_mqtt_client, mock_db_session):
    # Mock subscriptions
    mock_sub_result = MagicMock()
    mock_sub_scalars = MagicMock()
    mock_sub_scalars.all.return_value = ["u4pru", "ukmkr"]
    mock_sub_result.scalars.return_value = mock_sub_scalars

    # Mock high risk zones
    mock_risk_result = MagicMock()
    mock_risk_scalars = MagicMock()
    high_risk_zone = CurrentFireRisk(
        geohash="u4pru", risk_category="High", risk_score=75.0
    )
    extreme_risk_zone = CurrentFireRisk(
        geohash="ukmkr", risk_category="Extreme", risk_score=95.0
    )
    mock_risk_scalars.all.return_value = [
        high_risk_zone,
        extreme_risk_zone,
    ]
    mock_risk_result.scalars.return_value = mock_risk_scalars

    # Configure session.execute to return different results based on the query type
    mock_db_session.execute.side_effect = [mock_sub_result, mock_risk_result]

    await process_mqtt_alerts(mock_db_session)

    # Verify mqtt client was called twice
    assert mock_mqtt_client.publish_alert.call_count == 2
    mock_mqtt_client.publish_alert.assert_any_call(
        geohash="u4pru", risk_level="High", risk_score=75.0
    )
    mock_mqtt_client.publish_alert.assert_any_call(
        geohash="ukmkr", risk_level="Extreme", risk_score=95.0
    )


@pytest.mark.asyncio
@patch("app.services.event_processor_service.mqtt_client")
async def test_process_mqtt_alerts_no_subscriptions(mock_mqtt_client, mock_db_session):
    # Mock empty subscriptions
    mock_sub_result = MagicMock()
    mock_sub_scalars = MagicMock()
    mock_sub_scalars.all.return_value = []
    mock_sub_result.scalars.return_value = mock_sub_scalars

    mock_db_session.execute.return_value = mock_sub_result

    await process_mqtt_alerts(mock_db_session)

    # Verify mqtt client was not called
    mock_mqtt_client.publish_alert.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.event_processor_service.thingspeak_client")
async def test_process_thingspeak_analytics(mock_thingspeak, mock_db_session):
    # 1. Mock analytics zones (placed at city coordinates for deterministic mapping)
    mock_zone_result = MagicMock()
    mock_zone_scalars = MagicMock()
    mock_zone_scalars.all.return_value = [
        MonitoredZone(
            geohash="gh1",
            is_analytics_target=True,
            center_lat=59.9139,
            center_lon=10.7522,
        ),
        MonitoredZone(
            geohash="gh2",
            is_analytics_target=True,
            center_lat=60.3913,
            center_lon=5.3221,
        ),
        MonitoredZone(
            geohash="gh3",
            is_analytics_target=True,
            center_lat=63.4305,
            center_lon=10.3951,
        ),
        MonitoredZone(
            geohash="gh4",
            is_analytics_target=True,
            center_lat=58.9700,
            center_lon=5.7331,
        ),
        MonitoredZone(
            geohash="gh5",
            is_analytics_target=True,
            center_lat=58.1462,
            center_lon=7.9952,
        ),
        MonitoredZone(
            geohash="gh6",
            is_analytics_target=True,
            center_lat=69.6492,
            center_lon=18.9553,
        ),
        MonitoredZone(
            geohash="gh7",
            is_analytics_target=True,
            center_lat=67.2800,
            center_lon=14.4050,
        ),
    ]
    mock_zone_result.scalars.return_value = mock_zone_scalars

    # 2. Mock current risk rows for mapped cities (field1..field7)
    mock_risk_result = MagicMock()
    mock_risk_scalars = MagicMock()
    mock_risk_scalars.all.return_value = [
        CurrentFireRisk(geohash="gh1", risk_score=10.0),
        CurrentFireRisk(geohash="gh2", risk_score=20.0),
        CurrentFireRisk(geohash="gh3", risk_score=30.0),
        CurrentFireRisk(geohash="gh4", risk_score=40.0),
        CurrentFireRisk(geohash="gh5", risk_score=50.0),
        CurrentFireRisk(geohash="gh6", risk_score=60.0),
        CurrentFireRisk(geohash="gh7", risk_score=70.0),
    ]
    mock_risk_result.scalars.return_value = mock_risk_scalars

    # 3. Mock national average
    mock_avg_result = MagicMock()
    mock_avg_result.scalar_one_or_none.return_value = 45.0

    # Setup the session.execute side effects
    mock_db_session.execute.side_effect = [
        mock_zone_result,
        mock_risk_result,
        mock_avg_result,
    ]

    await process_thingspeak_analytics(mock_db_session)

    # Verify ThingSpeak was called with fixed city fields + national average.
    mock_thingspeak.push_data.assert_called_once_with(
        {
            "field1": 10.0,
            "field2": 20.0,
            "field3": 30.0,
            "field4": 40.0,
            "field5": 50.0,
            "field6": 60.0,
            "field7": 70.0,
            "field8": 45.0,
        }
    )


@pytest.mark.asyncio
@patch("app.services.event_processor_service.thingspeak_client")
async def test_process_thingspeak_analytics_falls_back_to_regional_zones(
    mock_thingspeak, mock_db_session
):
    # 1) analytics-target query returns empty
    empty_zone_result = MagicMock()
    empty_zone_scalars = MagicMock()
    empty_zone_scalars.all.return_value = []
    empty_zone_result.scalars.return_value = empty_zone_scalars

    # 2) fallback regional query returns city-aligned zones
    regional_zone_result = MagicMock()
    regional_zone_scalars = MagicMock()
    regional_zone_scalars.all.return_value = [
        MonitoredZone(
            geohash="gh1", is_regional=True, center_lat=59.9139, center_lon=10.7522
        ),
        MonitoredZone(
            geohash="gh2", is_regional=True, center_lat=60.3913, center_lon=5.3221
        ),
        MonitoredZone(
            geohash="gh3", is_regional=True, center_lat=63.4305, center_lon=10.3951
        ),
        MonitoredZone(
            geohash="gh4", is_regional=True, center_lat=58.9700, center_lon=5.7331
        ),
        MonitoredZone(
            geohash="gh5", is_regional=True, center_lat=58.1462, center_lon=7.9952
        ),
        MonitoredZone(
            geohash="gh6", is_regional=True, center_lat=69.6492, center_lon=18.9553
        ),
        MonitoredZone(
            geohash="gh7", is_regional=True, center_lat=67.2800, center_lon=14.4050
        ),
    ]
    regional_zone_result.scalars.return_value = regional_zone_scalars

    # 3) current risk rows for mapped geohashes
    mock_risk_result = MagicMock()
    mock_risk_scalars = MagicMock()
    mock_risk_scalars.all.return_value = [
        CurrentFireRisk(geohash="gh1", risk_score=11.0),
        CurrentFireRisk(geohash="gh2", risk_score=22.0),
        CurrentFireRisk(geohash="gh3", risk_score=33.0),
        CurrentFireRisk(geohash="gh4", risk_score=44.0),
        CurrentFireRisk(geohash="gh5", risk_score=55.0),
        CurrentFireRisk(geohash="gh6", risk_score=66.0),
        CurrentFireRisk(geohash="gh7", risk_score=77.0),
    ]
    mock_risk_result.scalars.return_value = mock_risk_scalars

    # 4) national average
    mock_avg_result = MagicMock()
    mock_avg_result.scalar_one_or_none.return_value = 50.5

    mock_db_session.execute.side_effect = [
        empty_zone_result,
        regional_zone_result,
        mock_risk_result,
        mock_avg_result,
    ]

    await process_thingspeak_analytics(mock_db_session)

    mock_thingspeak.push_data.assert_called_once_with(
        {
            "field1": 11.0,
            "field2": 22.0,
            "field3": 33.0,
            "field4": 44.0,
            "field5": 55.0,
            "field6": 66.0,
            "field7": 77.0,
            "field8": 50.5,
        }
    )
