import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.background import redis_listener_task
from app.db.database import create_db_and_tables
from app.routers import history_router, risk_router, subscription, zones
from app.services.mqtt_service import mqtt_client
from config import settings

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    print("FireGuard API starting up...")
    # Ensure all tables (like user_subscriptions) exist
    await create_db_and_tables()

    # Connect to MQTT broker
    await mqtt_client.connect_async()

    # Start the Redis listener as a background task
    redis_task = asyncio.create_task(redis_listener_task())

    # Start MQTT test task if enabled
    mqtt_test_task = None
    if settings.MQTT_TEST_MODE:
        print("MQTT Test Mode enabled - starting 30s interval push...")
        from app.services.mqtt_test_service import mqtt_test_push_task

        mqtt_test_task = asyncio.create_task(mqtt_test_push_task())

    # Start ThingSpeak test task if enabled
    thingspeak_test_task = None
    if settings.THINGSPEAK_TEST_MODE:
        print("ThingSpeak Test Mode enabled - starting 1min interval push...")
        from app.services.thingspeak_test_service import thingspeak_test_push_task

        thingspeak_test_task = asyncio.create_task(thingspeak_test_push_task())

    yield

    # Shutdown: Clean up resources
    print("FireGuard API shutting down...")

    # Stop the Redis listener task
    redis_task.cancel()
    try:
        await redis_task
    except asyncio.CancelledError:
        print("Redis listener task successfully cancelled.")

    # Stop MQTT test task if it was started
    if mqtt_test_task:
        mqtt_test_task.cancel()
        try:
            await mqtt_test_task
        except asyncio.CancelledError:
            print("MQTT test task successfully cancelled.")

    # Stop ThingSpeak test task if it was started
    if thingspeak_test_task:
        thingspeak_test_task.cancel()
        try:
            await thingspeak_test_task
        except asyncio.CancelledError:
            print("ThingSpeak test task successfully cancelled.")

    # Disconnect from MQTT
    mqtt_client.stop()


def create_app() -> FastAPI:
    fastapi_app = FastAPI(
        title="FireGuard API",
        description="Fire risk calculation service",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs/",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Get allowed origins from env, defaulting to development settings
    origins_str = os.getenv(
        "BACKEND_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )

    # split the string into a list
    origins = [origin.strip() for origin in origins_str.split(",")]

    # Configure CORS for Frontend
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create central API V1 Router
    api_v1_router = APIRouter(prefix="/api/v1")

    # Root API discovery
    @api_v1_router.get("/", tags=["Discovery"])
    async def api_root(request: Request):
        from app.utils.hateoas import create_links, get_base_url

        base_url = get_base_url(request)
        version = base_url.split("/")[-1] if "/" in base_url else "v1"

        links = create_links(
            request,
            "/",
            others=[
                {"href": "/risk/coords", "rel": "risk-by-coords"},
                {"href": "/zones/", "rel": "zones"},
                {
                    "href": "/zones/history",
                    "rel": "zones-history",
                },  # Public, for regional zones history
                {
                    "href": "/history/",
                    "rel": "history-all-readings",
                },  # Public, for all historical readings
                {
                    "href": "/users/me/subscriptions/",
                    "rel": "subscriptions",
                },  # Protected, but discoverable
            ],
        )
        return {
            "message": f"Welcome to FireGuard API {version}",
            "@context": {
                "@vocab": "https://schema.org/",
                "EntryPoint": "https://schema.org/EntryPoint",
            },
            "_links": links,
        }

    # Include versioned sub-routers
    api_v1_router.include_router(risk_router.router)
    api_v1_router.include_router(zones.router)
    api_v1_router.include_router(subscription.router)
    api_v1_router.include_router(history_router.router)

    # Include the main API router into the app
    fastapi_app.include_router(api_v1_router)

    return fastapi_app


app = create_app()
