from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import get_current_user
from app.db.database import get_db
from app.main import app

# Mock data
MOCK_USER = {"sub": "test-user-id", "preferred_username": "testuser"}
MOCK_GEOHASH = "u4pru"


@pytest.fixture
def mock_risk_reading():
    class Reading:
        def __init__(self):
            self.geohash = MOCK_GEOHASH
            self.latitude = 60.3913
            self.longitude = 5.3221
            self.risk_score = 0.5
            self.risk_category = "Moderate"
            self.ttf = 300.0
            self.prediction_timestamp = datetime.now(timezone.utc)
            self.updated_at = datetime.now(timezone.utc)

    return Reading()


@pytest.fixture
def mock_auth():
    async def override_get_current_user():
        return MOCK_USER

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_db_dep():
    async def override_get_db():
        mock_db = AsyncMock()
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
