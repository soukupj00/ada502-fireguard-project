import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import create_db_and_tables
from app.routers import risk_router, subscription, zones


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources (e.g., ML models, DB connections)
    print("FireGuard API starting up...")
    # Ensure all tables (like user_subscriptions) exist
    await create_db_and_tables()
    yield
    # Shutdown: Clean up resources
    print("FireGuard API shutting down...")


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
    # In docker-compose, we can pass "http://<YOUR_IP>" or "*"
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
                {"href": "/users/me/subscriptions/", "rel": "subscriptions"},
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

    # Include the main API router into the app
    fastapi_app.include_router(api_v1_router)

    return fastapi_app


app = create_app()
