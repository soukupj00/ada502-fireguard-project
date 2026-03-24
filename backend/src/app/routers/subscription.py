from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db.database import get_db
from app.schemas import (
    SubscriptionRequest,
    SubscriptionResponse,
    UserSubscriptionListResponse,
)
from app.services.subscription_service import (
    get_user_subscriptions_logic,
    subscribe_to_location_logic,
)

router = APIRouter(prefix="/subscribe", tags=["Subscription"])


@router.post("/", response_model=SubscriptionResponse)
async def subscribe_to_location(
    payload: SubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> SubscriptionResponse:
    """
    Subscribe to a location for fire risk monitoring.

    If the location is not already monitored, it will be added to the monitored zones.
    """
    user_id = user.get("sub")
    return await subscribe_to_location_logic(db, payload, user_id)


@router.get("/me", response_model=UserSubscriptionListResponse)
async def get_my_subscriptions(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> UserSubscriptionListResponse:
    """
    Get all active subscriptions for the currently authenticated user.
    """
    user_id = user.get("sub")
    return await get_user_subscriptions_logic(db, user_id)
