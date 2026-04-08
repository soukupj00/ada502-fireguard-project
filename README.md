# FireGuard

FireGuard is a fire-risk monitoring and analytics system. It calculates fire risk from weather data, stores hourly readings, exposes a REST API for clients, and distributes alerts/analytics through MQTT and ThingSpeak.

## What this repository contains

- **Frontend**: a React + Vite web app for browsing fire risk data and subscriptions.
- **Backend**: a FastAPI REST API with HATEOAS links and authentication-aware endpoints.
- **Intelligence System**: a background worker that fetches MET Norway data, calculates fire risk, and writes results to the database.
- **PostgreSQL**: shared persistence for current and historical readings.
- **Redis**: event bus and SSE/MQTT orchestration channel.
- **Keycloak**: authentication and authorization.
- **HiveMQ**: MQTT broker used for fire alert delivery.
- **ThingSpeak**: analytics channel used to visualize city and national fire-risk trends.

## Architecture overview

The runtime flow is:

1. The **Intelligence System** fetches weather data and calculates the fire risk score.
2. The result is stored in PostgreSQL as the latest reading and historical rows.
3. When the hourly calculation completes, the worker publishes a Redis event.
4. The **Backend** listens for that Redis event and orchestrates downstream work.
5. The backend publishes MQTT alerts to **HiveMQ** for subscribed users when risk levels are high enough.
6. The backend also pushes analytics to **ThingSpeak** for:
   - Oslo
   - Bergen
   - Trondheim
   - Stavanger
   - Kristiansand
   - Tromsø
   - Bodø
   - National average
7. The REST API remains the main entry point for the frontend, with HATEOAS links guiding navigation between related resources.

## REST API and HATEOAS

The backend exposes versioned endpoints under `/api/v1/`.
Common entry points include:

- `GET /api/v1/` — API discovery document with HATEOAS links
- `GET /api/v1/risk/coords?latitude=&longitude=` — latest risk by coordinates
- `GET /api/v1/risk/{geohash}` — latest risk by geohash
- `GET /api/v1/risk/{geohash}/history` — historical readings for a single location
- `GET /api/v1/zones/` — GeoJSON for monitored zones
- `GET /api/v1/zones/history` — historical readings for monitored zones
- `GET /api/v1/history/` — historical readings collection endpoint
- `POST /api/v1/users/me/subscriptions/` — create a subscription
- `GET /api/v1/users/me/subscriptions/` — list subscriptions
- `DELETE /api/v1/users/me/subscriptions/{geohash}` — remove a subscription
- `GET /api/v1/users/me/subscriptions/{geohash}/stream` — SSE stream for subscription updates

Most successful responses include `_links` so clients can navigate without hardcoding every path.

## Project structure

- `backend/` — FastAPI app, routers, services, database layer, and HATEOAS helpers
- `frontend/` — browser UI
- `intelligence-system/` — background worker and risk model pipeline
- `docker-compose.yml` — local development stack
- `docker-compose.prod.yml` — production deployment stack
- `.github/workflows/ci.yml` — CI pipeline

## Running with Docker Compose

Docker Compose is the easiest way to run the full stack locally.

### Prerequisites

- Docker
- Docker Compose

### Start the development stack

From the repository root:

```bash
docker compose up --build
```

Useful services in development usually include:

- Frontend: `http://localhost:5173`
- Backend docs: `http://localhost:8000/api/docs/`
- Keycloak: `http://localhost:8080/auth`
- Redis: `localhost:6379`

### Production compose

For the production setup, use the production compose file:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Production should typically keep the test modes disabled:

```env
MQTT_TEST_MODE=false
THINGSPEAK_TEST_MODE=false
THINGSPEAK_BACKFILL_ON_STARTUP=false
```

## Running locally without Docker

If you want to run individual services directly:

### Backend

```bash
cd backend
uv sync
uv run fastapi dev src/app/main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Intelligence system

```bash
cd intelligence-system
uv sync
uv run python src/main.py
```

## HiveMQ MQTT integration

The backend connects to HiveMQ as an MQTT client using the environment variables defined in `backend/src/config.py`.

Key settings:

- `HIVEMQ_HOST`
- `HIVEMQ_PORT`
- `HIVEMQ_USERNAME`
- `HIVEMQ_PASSWORD`
- `HIVEMQ_USE_TLS`
- `HIVEMQ_CA_CERT`
- `HIVEMQ_CLIENT_CERT`
- `HIVEMQ_CLIENT_KEY`
- `HIVEMQ_TLS_INSECURE`

Behavior:

- The backend subscribes to Redis events and publishes MQTT fire alerts when relevant.
- Users receive alert updates only for their active subscriptions.
- For testing, `MQTT_TEST_MODE=true` enables a faster alert loop.

## ThingSpeak analytics integration

ThingSpeak is used for fire-risk analytics dashboards.

Channel mapping:

- `field1` — Oslo
- `field2` — Bergen
- `field3` — Trondheim
- `field4` — Stavanger
- `field5` — Kristiansand
- `field6` — Tromsø
- `field7` — Bodø
- `field8` — National average

Relevant settings:

- `THINGSPEAK_WRITE_API_KEY`
- `THINGSPEAK_CHANNEL_ID`
- `THINGSPEAK_BACKFILL_ON_STARTUP`
- `THINGSPEAK_TEST_MODE`

Notes:

- The backend can push the latest analytics values after each hourly update.
- A startup backfill can populate the channel with recent history if enabled.
- For production, leave backfill disabled unless you explicitly want to seed historical points.

## Kubernetes setup

FireGuard can also be deployed on Kubernetes, for example with Minikube locally or a managed cluster in production.

### What you need

- Kubernetes cluster
- `kubectl`
- An ingress controller if you want browser access through a hostname
- Container images for the backend, frontend, and intelligence system

### Typical setup flow

1. Create Kubernetes secrets/config from your environment variables.
2. Build or publish the service images.
3. Deploy the database, Redis, Keycloak, backend, frontend, intelligence system, and broker dependencies.
4. Configure ingress so the browser can reach the frontend and API.
5. Point the application to cluster-internal service names for PostgreSQL, Redis, and other internal services.

### Example Minikube workflow

```bash
minikube start --driver=docker
minikube addons enable ingress
kubectl create secret generic fireguard-secrets --from-env-file=.env
eval $(minikube -p minikube docker-env)
docker compose build backend frontend intelligence
kubectl apply -f <your-k8s-manifests-directory>
minikube tunnel
```

If you use Kubernetes, make sure the environment variables for internal routing point to cluster service DNS names rather than `localhost`.

## Configuration

The backend reads configuration from environment variables or `.env`.

Common settings include:

- `DATABASE_URL`
- `REDIS_URL`
- `BACKEND_CORS_ORIGINS`
- `HIVEMQ_*`
- `THINGSPEAK_*`
- `MQTT_TEST_MODE`
- `THINGSPEAK_TEST_MODE`

In production, the usual defaults are:

- `MQTT_TEST_MODE=false`
- `THINGSPEAK_TEST_MODE=false`
- `THINGSPEAK_BACKFILL_ON_STARTUP=false`

## Development and testing notes

- `MQTT_TEST_MODE` enables a short interval MQTT push loop for testing alert delivery.
- `THINGSPEAK_TEST_MODE` enables a short interval ThingSpeak push loop for graph validation.
- `THINGSPEAK_BACKFILL_ON_STARTUP` controls whether the backend seeds historical ThingSpeak data when it starts.

## Testing and CI

The repository uses automated tests and CI for the backend, frontend, and intelligence system.

Pre-commit hooks can be installed with:

```bash
pip install pre-commit
pre-commit install
```

The CI workflow is defined in `.github/workflows/ci.yml`.

## Troubleshooting

- If the API starts but MQTT alerts do not appear, confirm the backend can reach HiveMQ and that the username/password are correct.
- If ThingSpeak receives no points, check `THINGSPEAK_WRITE_API_KEY`, `THINGSPEAK_CHANNEL_ID`, and the test/backfill flags.
- If Redis-driven SSE updates do not appear, verify that the backend and intelligence system share the same Redis instance and that the hourly event is being published.
- If Kubernetes traffic fails, check the ingress host, secret values, and service DNS names.
