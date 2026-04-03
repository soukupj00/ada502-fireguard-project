import asyncio
import logging
from typing import Any, AsyncGenerator, Sequence

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.models import Base, MonitoredZone
from config import settings

logger = logging.getLogger(__name__)

# Database connection
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


async def create_db_and_tables() -> None:
    """Creates the database and tables if they do not exist.

    Includes retry logic to handle timing issues where the database
    container is healthy but not yet accepting connections.
    """
    max_retries = 5
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # Keep older databases compatible with the current model definition.
                await conn.execute(
                    text(
                        """
                        ALTER TABLE monitored_zones
                        ADD COLUMN IF NOT EXISTS is_analytics_target
                        BOOLEAN NOT NULL DEFAULT FALSE
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
            logger.info("Database and tables created/verified successfully.")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Database connection attempt {attempt + 1}/{max_retries} "
                    f"failed: {e}. "
                    f"Retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    f"Failed to connect to database after {max_retries} attempts."
                )
                raise


async def get_monitored_zones() -> Sequence[Any]:
    """Returns all active monitored zones."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MonitoredZone))
        return result.scalars().all()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
