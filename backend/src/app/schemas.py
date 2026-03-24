from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    """HATEOAS Link Model"""

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


class FireRiskReadingSchema(BaseModel):
    """Schema for a fire risk reading."""

    geohash: str
    latitude: float
    longitude: float
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    ttf: float
    prediction_timestamp: datetime
    updated_at: datetime
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


# GeoJSON Models (with JSON-LD Context)


class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [lon, lat]


class GeoJSONProperties(BaseModel):
    geohash: str
    name: Optional[str] = None
    is_regional: bool
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    last_updated: Optional[datetime] = None


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: GeoJSONProperties
    # Optionally add context to each feature if needed, but usually it's on collections
    context: Optional[Dict[str, Any]] = Field(alias="@context", default=None)
    links: Optional[List[Link]] = Field(alias="_links", default=None)

    model_config = ConfigDict(populate_by_name=True)


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]
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
