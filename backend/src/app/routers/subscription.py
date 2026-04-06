from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_current_user_ws_or_sse
from app.db.database import get_db
from app.schemas import (
    GeoJSONFeatureCollection,
    SubscriptionRequest,
    SubscriptionResponse,
)
from app.services.subscription_service import (
    get_user_subscriptions_logic,
    subscribe_to_location_logic,
    unsubscribe_from_location_logic,
)
from app.utils.redis import redis_client

# Changed prefix for better RESTful structure
router = APIRouter(prefix="/users/me/subscriptions", tags=["User Subscriptions"])


@router.post(
    "/", response_model=SubscriptionResponse, status_code=status.HTTP_202_ACCEPTED
)
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


@router.delete("/{geohash}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    geohash: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> None:
    """
    Remove a subscription for the authenticated user.
    """
    user_id = user.get("sub")
    await unsubscribe_from_location_logic(db, geohash, user_id)
    return None


@router.get("/{geohash}/stream")
async def stream_subscription_updates(
    geohash: str,
    user: dict = Depends(get_current_user_ws_or_sse),
) -> StreamingResponse:
    """
    Streams fire risk updates for a specific geohash via Server-Sent Events.
    """

    async def event_generator():
        # Send the most recent known value first to avoid race conditions where
        # a publish happens before the client subscribes to Redis pubsub.
        cached = await redis_client.get(f"location_updates:last:{geohash}")
        if isinstance(cached, bytes):
            yield f"data: {cached.decode('utf-8')}\n\n"
            return
        if isinstance(cached, str):
            yield f"data: {cached}\n\n"
            return

        pubsub = redis_client.pubsub()
        channel_name = f"location_updates:{geohash}"
        await pubsub.subscribe(channel_name)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"].decode("utf-8")
                    yield f"data: {data}\n\n"
                    break  # Close stream after first update
        finally:
            await pubsub.unsubscribe(channel_name)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Forces Nginx to pass data instantly
        },
    )
