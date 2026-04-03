from typing import Any, AsyncGenerator, Dict, Sequence

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import settings
from utils.fire_risk_service import calculate_risk_score
from utils.grid_utils import generate_initial_zones

# Database connection
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


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
    last_updated: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WeatherDataReading(Base):
    """SQLAlchemy model for raw weather data readings."""

    __tablename__ = "weather_data_readings"

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, index=True)  # Can be geohash or city name
    latitude = Column(Float)
    longitude = Column(Float)
    data = Column(JSONB)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())


class FireRiskReading(Base):
    """SQLAlchemy model for fire risk readings (History)."""

    __tablename__ = "fire_risk_readings"

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, index=True)  # Can be geohash or city name
    latitude = Column(Float)
    longitude = Column(Float)
    ttf = Column(Float)
    rh_in = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_category = Column(String, nullable=True)
    prediction_timestamp = Column(DateTime(timezone=True))
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())


class CurrentFireRisk(Base):
    """
    Stores the MOST RECENT fire risk calculation for each zone.
    This table is optimized for fast lookups by the backend API.
    """

    __tablename__ = "current_fire_risks"

    geohash = Column(String, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    ttf = Column(Float)
    rh_in = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_category = Column(String, nullable=True)
    prediction_timestamp = Column(DateTime(timezone=True))
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


async def create_db_and_tables() -> None:
    """Creates the database and tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add missing columns for backward compatibility
        from sqlalchemy import text

        await conn.execute(
            text(
                """
                ALTER TABLE fire_risk_readings
                ADD COLUMN IF NOT EXISTS rh_in DOUBLE PRECISION
                """
            )
        )
        await conn.execute(
            text(
                """
                ALTER TABLE current_fire_risks
                ADD COLUMN IF NOT EXISTS rh_in DOUBLE PRECISION
                """
            )
        )


async def seed_initial_zones() -> None:
    """
    Populates the database with initial regional zones if empty.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MonitoredZone).limit(1))
        if result.first() is None:
            initial_zones = generate_initial_zones()
            for zone_data in initial_zones:
                zone = MonitoredZone(**zone_data)
                db.add(zone)
            await db.commit()


async def get_monitored_zones() -> Sequence[Any]:
    """Returns all active monitored zones."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MonitoredZone))
        return result.scalars().all()


async def get_zone_by_geohash(geohash: str) -> MonitoredZone | None:
    """Returns a single monitored zone by its geohash."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MonitoredZone).where(MonitoredZone.geohash == geohash)
        )
        return result.scalar_one_or_none()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def save_weather_data(
    location_name: str, lat: float, lon: float, weather_json: Dict[str, Any]
) -> None:
    """Saves the raw weather data for a given location to the database."""
    async with AsyncSessionLocal() as db:
        db_reading = WeatherDataReading(
            location_name=location_name,
            latitude=lat,
            longitude=lon,
            data=weather_json,
        )
        db.add(db_reading)
        await db.commit()


async def save_risk_data(
    location_name: str, lat: float, lon: float, risk_result: Dict[str, Any]
) -> None:
    """
    Saves the fire risk data to the history table AND updates the current risk table.
    """
    # Calculate risk score and category
    ttf = risk_result["ttf"]
    rh_in = risk_result.get("rh_in")
    risk_score, risk_category = calculate_risk_score(ttf)

    async with AsyncSessionLocal() as db:
        # 1. Insert into History Table
        db_reading = FireRiskReading(
            location_name=location_name,
            latitude=lat,
            longitude=lon,
            ttf=ttf,
            rh_in=rh_in,
            risk_score=risk_score,
            risk_category=risk_category,
            prediction_timestamp=risk_result["timestamp"],
        )
        db.add(db_reading)

        # 2. Insert into Current Risk Table
        stmt = insert(CurrentFireRisk).values(
            geohash=location_name,
            latitude=lat,
            longitude=lon,
            ttf=ttf,
            rh_in=rh_in,
            risk_score=risk_score,
            risk_category=risk_category,
            prediction_timestamp=risk_result["timestamp"],
        )

        # If geohash exists, update the values
        stmt = stmt.on_conflict_do_update(
            index_elements=["geohash"],
            set_={
                "ttf": stmt.excluded.ttf,
                "rh_in": stmt.excluded.rh_in,
                "risk_score": stmt.excluded.risk_score,
                "risk_category": stmt.excluded.risk_category,
                "prediction_timestamp": stmt.excluded.prediction_timestamp,
                "updated_at": func.now(),
            },
        )

        await db.execute(stmt)
        await db.commit()


async def get_latest_readings(
    location_name: str, limit: int = 1
) -> dict[str, Sequence[Any]]:
    """
    Debug function to get the latest weather and fire risk readings for a location.
    """
    async with AsyncSessionLocal() as db:
        weather_result = await db.execute(
            select(WeatherDataReading)
            .where(WeatherDataReading.location_name == location_name)
            .order_by(WeatherDataReading.recorded_at.desc())
            .limit(limit)
        )
        weather_readings = weather_result.scalars().all()

        risk_result = await db.execute(
            select(FireRiskReading)
            .where(FireRiskReading.location_name == location_name)
            .order_by(FireRiskReading.recorded_at.desc())
            .limit(limit)
        )
        risk_readings = risk_result.scalars().all()

        return {
            "weather_data": weather_readings,
            "fire_risk_data": risk_readings,
        }
