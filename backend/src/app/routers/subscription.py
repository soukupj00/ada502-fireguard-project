from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db.database import get_db
from app.schemas import (
    GeoJSONFeatureCollection,
    SubscriptionRequest,
    SubscriptionResponse,
)
from app.services.subscription_service import (
    get_user_subscriptions_logic,
    subscribe_to_location_logic,
)

# Changed prefix for better RESTful structure
router = APIRouter(prefix="/users/me/subscriptions", tags=["User Subscriptions"])


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    request: Request,
    payload: SubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> SubscriptionResponse:
    """
    Create a new subscription for the authenticated user.
    """
    user_id = user.get("sub")
    return await subscribe_to_location_logic(db, payload, user_id, request)


@router.get("/", response_model=GeoJSONFeatureCollection, response_model_by_alias=True)
async def get_my_subscriptions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> GeoJSONFeatureCollection:
    """
    Get all active subscriptions for the currently authenticated user in GeoJSON format.
    """
    user_id = user.get("sub")
    return await get_user_subscriptions_logic(db, user_id, request)
