from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models, providing a common metadata store."""

    pass


class MonitoredZone(Base):
    """
    Represents a geographic zone (grid cell) that we are actively monitoring.
    """

    __tablename__ = "monitored_zones"

    geohash: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    center_lat: Mapped[float] = mapped_column(Float, nullable=False)
    center_lon: Mapped[float] = mapped_column(Float, nullable=False)
    is_regional: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # True = Tier 1 (Map), False = Tier 2 (User)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    is_analytics_target: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # True if this zone's data should be pushed to ThingSpeak
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WeatherDataReading(Base):
    """
    Represents a single reading of raw weather data from an external API.
    """

    __tablename__ = "weather_data_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location_name: Mapped[str] = mapped_column(String, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FireRiskReading(Base):
    """
    Represents the calculated fire risk for a specific location (History).
    """

    __tablename__ = "fire_risk_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location_name: Mapped[str] = mapped_column(String, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    ttf: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_category: Mapped[str | None] = mapped_column(String, nullable=True)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CurrentFireRisk(Base):
    """
    Stores the MOST RECENT fire risk calculation for each zone.
    This table is optimized for fast lookups by the backend API.
    """

    __tablename__ = "current_fire_risks"

    geohash: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    ttf: Mapped[float] = mapped_column(Float)
    # Compatibility with intelligence-system upsert payloads.
    rh_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_category: Mapped[str | None] = mapped_column(String, nullable=True)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserSubscription(Base):
    """
    Links a user to a specific geohash they want to monitor.
    """

    __tablename__ = "user_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "geohash", name="uix_user_geohash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String, index=True
    )  # Subject (sub) from Keycloak JWT
    geohash: Mapped[str] = mapped_column(String, ForeignKey("monitored_zones.geohash"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Optional: Relationship back to the zone
    zone: Mapped[MonitoredZone] = relationship()
