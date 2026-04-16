"""Adapters between MET weather payloads and the Fire Risk Computation Model."""

import datetime
import logging
from typing import Any, Dict, Tuple

from frcm.datamodel import model as dm
from frcm.fireriskmodel.compute import compute

logger = logging.getLogger(__name__)


def transform_met_data_to_model(met_json: Dict[str, Any]) -> dm.WeatherData:
    """
    Convert MET.no timeseries JSON into FRCM ``WeatherData`` input.

    The function keeps the full forecast sequence and normalizes timestamps to
    timezone-aware datetimes expected by the model.
    """
    timeseries = met_json["properties"]["timeseries"]
    data_points = []

    for entry in timeseries:
        time_str = entry["time"]
        # MET.no uses 'Z' for UTC, fromisoformat handles +00:00
        dt = datetime.datetime.fromisoformat(time_str.replace("Z", "+00:00"))

        instant_details = entry["data"]["instant"]["details"]

        # Create WeatherDataPoint with fields matching the datamodel
        dp = dm.WeatherDataPoint(
            timestamp=dt,
            temperature=instant_details.get("air_temperature"),
            humidity=instant_details.get("relative_humidity"),
            wind_speed=instant_details.get("wind_speed", 0.0),
        )
        data_points.append(dp)

    # Wrap the list of points in the WeatherData container
    return dm.WeatherData(data=data_points)


def calculate_risk(met_json: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Run risk computation end-to-end and return the current prediction snapshot.

    The FRCM output contains a forecast sequence; this function returns the
    second sample, which represents the first computed point after model
    initialization.
    """
    try:
        # 1. Transform Data
        weather_data = transform_met_data_to_model(met_json)

        # 2. Run the FRCM Simulation
        # This returns a dm.FireRiskPrediction object containing a list of risks
        prediction_result = compute(weather_data)

        # 3. Extract the most relevant result
        # The compute function returns a simulation for the whole forecast period.
        # We take the second element as the "current" risk, as the first is
        # based on initial hardcoded parameters.
        if prediction_result.firerisks and len(prediction_result.firerisks) > 1:
            current_risk = prediction_result.firerisks[1]

            return {
                "timestamp": current_risk.timestamp,
                "ttf": current_risk.ttf,  # Time To Flashover (Lower = Higher Risk)
            }

        return None

    except Exception as e:
        logger.error(f"Error in risk calculation: {e}")
        return None


def calculate_risk_score(ttf: float) -> Tuple[float, str]:
    """
    Calculates a normalized risk score (0-100) and
    category based on Time To Flashover (TTF).

    TTF is expressed in minutes. Lower TTF means higher risk.

    Args:
        ttf: Time To Flashover in minutes.

    Returns:
        A tuple containing:
        - risk_score: A float between 0 and 100 (100 = Extreme Risk).
        - risk_category: A string description (Low, Moderate, High, Extreme).
    """
    if ttf <= 0:
        return 100.0, "Extreme"

    # Define thresholds
    # These are heuristic values and can be tuned.
    if ttf < 5:
        # Extreme Risk: TTF < 5 mins
        # Map 0-5 mins to 80-100 score
        score = 100 - (ttf / 5) * 20
        category = "Extreme"
    elif ttf < 15:
        # High Risk: 5-15 mins
        # Map 5-15 mins to 60-80 score
        score = 80 - ((ttf - 5) / 10) * 20
        category = "High"
    elif ttf < 30:
        # Moderate Risk: 15-30 mins
        # Map 15-30 mins to 30-60 score
        score = 60 - ((ttf - 15) / 15) * 30
        category = "Moderate"
    else:
        # Low Risk: > 30 mins
        # Map 30+ mins to 0-30 score
        # Decay function: score approaches 0 as ttf increases
        score = max(0.0, 30 - ((ttf - 30) / 30) * 30)
        category = "Low"

    return round(score, 1), category
