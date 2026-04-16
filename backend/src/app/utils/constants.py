"""Shared constants and lookup tables for risk assessment and analytics.

Defines risk level classifications (Low, Moderate, High, Extreme), cities
included in ThingSpeak analytics, and field mappings for third-party data
integrations. Enables consistent risk categorization across backend and
intelligence system.
"""

from app.schemas import RiskLegend, RiskLevel

RISK_LEGEND_DATA = RiskLegend(
    levels=[
        RiskLevel(
            category="Low",
            score_range="0-30",
            description="Time to flashover is predicted to be greater than 30 minutes."
            "Normal conditions.",
        ),
        RiskLevel(
            category="Moderate",
            score_range="30-60",
            description="Time to flashover is predicted to be "
            "between 15 and 30 minutes."
            "Elevated caution is advised.",
        ),
        RiskLevel(
            category="High",
            score_range="60-80",
            description="Time to flashover is predicted to be between 5 and 15 minutes."
            "Significant risk of rapid fire spread.",
        ),
        RiskLevel(
            category="Extreme",
            score_range="80-100",
            description="Time to flashover is predicted to be under 5 minutes. "
            "Critical emergency conditions; immediate action required.",
        ),
    ]
)

ANALYTICS_CITIES = [
    {"name": "Oslo", "latitude": 59.9139, "longitude": 10.7522},
    {"name": "Bergen", "latitude": 60.3913, "longitude": 5.3221},
    {"name": "Trondheim", "latitude": 63.4305, "longitude": 10.3951},
    {"name": "Stavanger", "latitude": 58.9700, "longitude": 5.7331},
    {"name": "Kristiansand", "latitude": 58.1462, "longitude": 7.9952},
    {"name": "Tromsø", "latitude": 69.6492, "longitude": 18.9553},
    {"name": "Bodø", "latitude": 67.2800, "longitude": 14.4050},
]

# Fixed ThingSpeak channel mapping:
# field1..field7 are city risk scores, field8 is national average.
THINGSPEAK_CITY_FIELD_ORDER = [
    "Oslo",
    "Bergen",
    "Trondheim",
    "Stavanger",
    "Kristiansand",
    "Tromsø",
    "Bodø",
]

THINGSPEAK_NATIONAL_AVERAGE_FIELD = "field8"

THINGSPEAK_CITY_COORDS = {
    city["name"]: (city["latitude"], city["longitude"]) for city in ANALYTICS_CITIES
}
