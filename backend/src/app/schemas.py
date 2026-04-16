"""Pydantic schemas for API payloads, GeoJSON documents, and HATEOAS metadata."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FireRiskRequest(BaseModel):
    """Request model for fire risk prediction."""

    temperature: float = Field(
        ...,
        examples=[25.5],
        description="Temperature in Celsius",
    )
    humidity: float = Field(
        ...,
        examples=[60.0],
        description="Relative humidity in percent",
    )
    wind_speed: float = Field(
        ...,
        examples=[10.0],
        description="Wind speed in km/h",
    )


class Link(BaseModel):
    """HATEOAS link object used in ``_links`` collections."""

    href: str
    rel: str
    type: str = "application/json"


class FireRiskResponse(BaseModel):
    """Response model for fire risk prediction."""

    risk_score: float = Field(
        ...,
        examples=[0.75],
        description="Calculated fire risk score (0 to 1)",
    )
    time_to_flashover: float = Field(
        ...,
        examples=[300.5],
        description="Estimated time to flashover in seconds",
    )
    recommendation: str = Field(
        ...,
        examples=["High risk: consider evacuation."],
        description="Plain-text safety recommendation",
    )
    timestamp: datetime = Field(..., description="Timestamp of the prediction")
    context: Dict[str, Any] = Field(
        alias="@context",
        default={
            "@vocab": "https://schema.org/",
            "FireRiskResponse": "https://schema.org/Observation",
            "risk_score": "https://schema.org/value",
            "timestamp": "https://schema.org/datePublished",
        },
    )
    links: Optional[List[Link]] = Field(alias="_links", default=None)

    model_config = ConfigDict(populate_by_name=True)


class MonitoredZoneSchema(BaseModel):
    """Schema for a monitored zone."""

    geohash: str
    center_lat: float
    center_lon: float
    is_regional: bool
    name: Optional[str] = None
    last_updated: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- New Models for Risk Legend ---


class RiskLevel(BaseModel):
    """Describes a single level of risk."""

    category: str = Field(
        ..., description="The name of the risk category (e.g., 'Low', 'Moderate')."
    )
    score_range: str = Field(
        ..., description="The score range for this category (e.g., '0-30')."
    )
    description: str = Field(
        ..., description="A brief explanation of what this risk level means."
    )


class RiskLegend(BaseModel):
    """Provides a key for interpreting risk scores and categories."""

    title: str = "Fire Risk Legend"
    description: str = (
        "This legend explains the risk score, which is a "
        "normalized value from 0-100 derived from the "
        "Time To Flashover (TTF)."
    )
    levels: List[RiskLevel]


class FireRiskReadingSchema(BaseModel):
    """Schema for a fire risk reading.

    The database model uses `location_name` for the stored geohash; allow
    `location_name` as an alias so Pydantic can validate SQLAlchemy objects
    without requiring changes to the DB models.
    """

    # Geohash (external name). The DB model stores this as `location_name` so
    # we coerce inputs that provide `location_name` (or SQLAlchemy objects)
    # to this schema field below.
    geohash: str
    latitude: float
    longitude: float
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    ttf: Optional[float] = None
    prediction_timestamp: datetime
    updated_at: Optional[datetime] = None
    risk_legend: Optional[RiskLegend] = Field(
        None, description="A key for interpreting the risk scores and categories."
    )
    context: Dict[str, Any] = Field(
        alias="@context",
        default={
            "@vocab": "https://schema.org/",
            "FireRiskReading": "https://schema.org/Observation",
            "geohash": "https://schema.org/identifier",
            "risk_score": "https://schema.org/value",
        },
    )
    links: Optional[List[Link]] = Field(alias="_links", default=None)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    def _map_location_name(cls, v):
        """Coerce inputs that use `location_name` (DB models) into the
        expected dict shape with `geohash` so validation succeeds and
        output uses the `geohash` key.
        """
        # If it's a mapping (e.g., dict) with location_name, move it to geohash
        try:
            if isinstance(v, dict):
                if "location_name" in v and "geohash" not in v:
                    v["geohash"] = v.pop("location_name")
                return v
        except Exception:
            pass

        # If it's an object (like SQLAlchemy model), extract attributes
        if hasattr(v, "location_name") or hasattr(v, "geohash"):
            return {
                "geohash": getattr(v, "geohash", None)
                or getattr(v, "location_name", None),
                "latitude": getattr(v, "latitude", None),
                "longitude": getattr(v, "longitude", None),
                "risk_score": getattr(v, "risk_score", None),
                "risk_category": getattr(v, "risk_category", None),
                "ttf": getattr(v, "ttf", None),
                "prediction_timestamp": getattr(v, "prediction_timestamp", None),
                "updated_at": getattr(v, "updated_at", None),
            }

        return v


class SubscriptionRequest(BaseModel):
    """Request model for user subscription."""

    latitude: Optional[float] = Field(
        None,
        examples=[60.3913],
        description="Latitude of the location",
    )
    longitude: Optional[float] = Field(
        None,
        examples=[5.3221],
        description="Longitude of the location",
    )
    geohash: Optional[str] = Field(
        None,
        examples=["u4pruydqqvj"],
        description="Geohash of the location",
    )


class SubscriptionResponse(BaseModel):
    """Response model for user subscription."""

    geohash: str
    status: str
    message: str
    current_risk: Optional[float] = None
    context: Dict[str, Any] = Field(
        alias="@context",
        default={
            "@vocab": "https://schema.org/",
            "SubscriptionResponse": "https://schema.org/Action",
            "geohash": "https://schema.org/identifier",
            "status": "https://schema.org/actionStatus",
        },
    )
    links: Optional[List[Link]] = Field(alias="_links", default=None)

    model_config = ConfigDict(populate_by_name=True)


class UserSubscriptionListResponse(BaseModel):
    """Response model for listing a user's subscriptions."""

    geohashes: List[str]
    links: Optional[List[Link]] = Field(alias="_links", default=None)

    model_config = ConfigDict(populate_by_name=True)


# --- GeoJSON Models ---


class GeoJSONGeometry(BaseModel):
    """GeoJSON geometry object used by zone and history features."""

    type: str = "Point"
    coordinates: List[float]  # [lon, lat]


class GeoJSONProperties(BaseModel):
    """Properties payload for each GeoJSON zone feature."""

    geohash: str
    name: Optional[str] = None
    is_regional: bool
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    last_updated: Optional[datetime] = None


class GeoJSONFeature(BaseModel):
    """GeoJSON feature representing one monitored zone."""

    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: GeoJSONProperties
    # Optionally add context to each feature if needed, but usually it's on collections
    context: Optional[Dict[str, Any]] = Field(alias="@context", default=None)
    links: Optional[List[Link]] = Field(alias="_links", default=None)

    model_config = ConfigDict(populate_by_name=True)


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON feature collection wrapper returned by zone/subscription APIs."""

    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]
    risk_legend: Optional[RiskLegend] = Field(
        None, description="A key for interpreting the risk scores and categories."
    )
    context: Dict[str, Any] = Field(
        alias="@context",
        default={
            "@vocab": "https://purl.org/geojson/vocab#",
            "FeatureCollection": "https://purl.org/geojson/vocab#FeatureCollection",
            "Feature": "https://purl.org/geojson/vocab#Feature",
            "Point": "https://purl.org/geojson/vocab#Point",
        },
    )
    links: Optional[List[Link]] = Field(alias="_links", default=None)

    model_config = ConfigDict(populate_by_name=True)
