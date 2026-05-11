# FireGuard

FireGuard is a fire-risk monitoring and analytics platform.
It combines a React frontend, FastAPI backend, Intelligence Worker, MQTT alerting, ThingSpeak IoT analytics, Keycloak auth, PostgreSQL database, Redis, and automatically generated documentation.

## Live Environment

- App URL: https://group10.ada502-fireguard.live/
- Docs URL (cluster): https://group10.ada502-fireguard.live/docs/
- Keycloak path (proxied): https://group10.ada502-fireguard.live/auth/
- API base (proxied): https://group10.ada502-fireguard.live/api/

## Generated documentation

- GitHub pages FireGuard Documentation: https://soukupj00.github.io/ada502-fireguard-project/

## Repository Components

- `frontend/`: React + Vite + TypeScript web UI.
- `backend/`: FastAPI API, auth-aware routes, subscriptions, SSE, MQTT orchestration.
- `intelligence-system/`: periodic weather ingestion and fire-risk computation.
- `docs/`: MkDocs + Material site and docs container setup.
- `k8s-manifests/`: Kubernetes manifests for NREC/Minikube-style deployment.
- `.github/workflows/`: CI, image publishing, docs publishing, deployment automation.
- `realm-exports/`: Keycloak export files used for realm bootstrap/import.

## How the App Works

1. Intelligence worker fetches and processes weather inputs.
2. Worker computes fire-risk and writes current + historical data to PostgreSQL.
3. Worker triggers downstream events via Redis.
4. Backend reacts to events and serves updated data via API and SSE.
5. Backend publishes alert messages to HiveMQ topics for subscribed users.
6. Backend pushes analytics to ThingSpeak fields.
7. Frontend consumes API, SSE, MQTT, and ThingSpeak read endpoints to render live risk and trends.

## Prerequisites

### General

- Git
- Docker + Docker Compose plugin
- Node.js 20+ (for local frontend/docs generation)
- Python 3.12 + `uv` (for local backend/intelligence/docs commands)

### For Kubernetes/Minikube

- `kubectl`
- `minikube`
- NGINX ingress addon enabled in Minikube

## Required Configuration

The app can start with many defaults, but full functionality requires proper secrets.

### Backend/worker critical variables

- `DATABASE_URL`
- `REDIS_URL`
- `HIVEMQ_HOST`, `HIVEMQ_PORT`
- `HIVEMQ_USERNAME`, `HIVEMQ_PASSWORD` (if broker auth enabled)
- `THINGSPEAK_WRITE_API_KEY`
- `THINGSPEAK_CHANNEL_ID`

### Frontend build/runtime variables

- `VITE_API_URL`
- `VITE_KEYCLOAK_URL`
- `VITE_MQTT_BROKER_URL`
- `VITE_MQTT_USERNAME`, `VITE_MQTT_PASSWORD`
- `VITE_THINGSPEAK_CHANNEL_ID`
- `VITE_THINGSPEAK_READ_API_KEY`

### Feature/test toggles

- `MQTT_TEST_MODE`
- `THINGSPEAK_TEST_MODE`
- `THINGSPEAK_BACKFILL_ON_STARTUP`

Recommended production values:

- `MQTT_TEST_MODE=false`
- `THINGSPEAK_TEST_MODE=false`
- `THINGSPEAK_BACKFILL_ON_STARTUP=false`

## Local Development with Docker Compose

This is the recommended local setup.

### 1. Create `.env.compose`

Create a root `.env.compose` file and provide at least:

```env
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=fireguard_db

KC_POSTGRES_USER=keycloak_user
KC_POSTGRES_PASSWORD=keycloak_password
KC_POSTGRES_DB=keycloak_db
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

DATABASE_URL=postgresql+asyncpg://user:password@db:5432/fireguard_db
REDIS_URL=redis://redis:6379/0

HIVEMQ_HOST=hivemq
HIVEMQ_PORT=1883
HIVEMQ_USERNAME=
HIVEMQ_PASSWORD=

THINGSPEAK_CHANNEL_ID=<your_channel_id>
THINGSPEAK_WRITE_API_KEY=<your_write_key>

VITE_API_URL=http://localhost:8000
VITE_KEYCLOAK_URL=http://localhost:8080/auth
VITE_MQTT_BROKER_URL=ws://localhost:8081/mqtt
VITE_MQTT_USERNAME=
VITE_MQTT_PASSWORD=
VITE_THINGSPEAK_CHANNEL_ID=<your_channel_id>
VITE_THINGSPEAK_READ_API_KEY=<your_read_key>
```

### 2. Run Docker Compose

```bash
docker compose --env-file .env.compose up --build
```

### 3. Local endpoints

- Frontend (Vite dev): http://localhost:5173
- Backend API docs: http://localhost:8000/api/docs/
- Keycloak: http://localhost:8080/auth/
- Docs container: http://localhost:8088

### 4. HiveMQ and Keycloak notes

- HiveMQ: compose and Minikube manifests disable remote JMX by default to avoid Java hostname resolution failures.
- Keycloak: local compose includes the `keycloak` service. If using external Keycloak, update `VITE_KEYCLOAK_URL` and related `KEYCLOAK_*` variables.

### 5. Seed Keycloak realm (recommended)

1. Open http://localhost:8080/auth/admin
2. Login with `KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD`
3. Realm selector -> Create realm -> Import
4. Import file: `realm-exports/realm-export-locahost.json`
5. Confirm realm `FireGuard` and clients `frontend-client` and `backend-client` exist

## Local Development with Minikube (use `fireguard.local`)

Use Minikube to test Kubernetes manifests locally with a local domain.

### 1. Start Minikube and enable ingress

```bash
minikube start --driver=docker
minikube addons enable ingress
```

### 2. Create Kubernetes secret from `.env.k8s`

```bash
kubectl create secret generic fireguard-secrets \
  --from-env-file=.env.k8s \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Apply manifests and local ingress

Apply core manifests first, then the local ingress file:

```bash
kubectl apply -f k8s-manifests/
kubectl apply -f k8s-manifests-local/ingress.local.yaml
```

### 3.1 Use a local frontend image for Minikube (recommended)

The default Kubernetes frontend deployment points to the production GHCR image, which may contain production `VITE_*` build values. For local Minikube, build and load a local frontend image and apply the local deployment override:

```bash
docker build \
  --build-arg VITE_API_URL=http://fireguard.local \
  --build-arg VITE_KEYCLOAK_URL=http://fireguard.local/auth \
  --build-arg VITE_MQTT_BROKER_URL=ws://fireguard.local/mqtt \
  --build-arg VITE_MQTT_USERNAME=${VITE_MQTT_USERNAME:-} \
  --build-arg VITE_MQTT_PASSWORD=${VITE_MQTT_PASSWORD:-} \
  --build-arg VITE_THINGSPEAK_CHANNEL_ID=${VITE_THINGSPEAK_CHANNEL_ID:-} \
  --build-arg VITE_THINGSPEAK_READ_API_KEY=${VITE_THINGSPEAK_READ_API_KEY:-} \
  -t ada502-fireguard-frontend:local \
  ./frontend

minikube image load ada502-fireguard-frontend:local
kubectl apply -f k8s-manifests-local/frontend-deployment.local.yaml
kubectl rollout restart deployment/frontend
kubectl rollout status deployment/frontend --timeout=120s
```

### 4. Map `fireguard.local` to Minikube IP

```bash
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"
sudo -- sh -c "printf '%s\t%s\n' $MINIKUBE_IP fireguard.local >> /etc/hosts"
```

### 5. Validate local Minikube setup

```bash
kubectl get pods -o wide
kubectl get svc
kubectl get ingress fireguard-ingress-local -o wide

kubectl rollout status deployment/backend --timeout=120s
kubectl rollout status deployment/frontend --timeout=120s
kubectl rollout status deployment/intelligence --timeout=120s
kubectl rollout status deployment/docs --timeout=120s

curl -fsS http://fireguard.local/ || echo 'frontend unreachable'
curl -fsS http://fireguard.local/api/docs/ || echo 'backend docs unreachable'
curl -fsS http://fireguard.local/auth/ || echo 'keycloak unreachable'
```

### 6. Import Keycloak realm for Minikube

If this is a fresh Keycloak instance, import the Kubernetes-local realm export:

```bash
kubectl port-forward svc/keycloak 8080:8080
```

Then open `http://localhost:8080/auth/admin` and import `realm-exports/realm-export-local-k8s.json`.

### 7. Troubleshooting

- `404` from browser: verify `/etc/hosts` includes `fireguard.local` and ingress host matches with `kubectl get ingress fireguard-ingress-local -o yaml`.
- Pending pods/PVCs: check with `kubectl describe pod <pod>` and `kubectl describe pvc <name>`.
- HiveMQ pending: verify PVC binding and node scheduling events.
- Keycloak realm import: `kubectl port-forward svc/keycloak 8080:8080` and import via UI.

### 8. Stop Minikube

When you're finished testing, you can stop the Minikube cluster temporarily or delete it entirely:

```bash
# Stop the cluster (keeps VM/image cache)
minikube stop

# Delete the cluster and free resources
minikube delete

# Remove the local hosts entry added earlier (if present)
sudo sed -i '/fireguard.local/d' /etc/hosts
```

## Documentation: Where to Find It

### Generated docs in repository

- Frontend generated API reference markdown:
  - `docs/frontend/reference/`
- Frontend catalog page:
  - `docs/frontend/api-catalog.md`

### Local docs preview

```bash
uv sync --project docs
npm --prefix frontend run docs:api
mkdir -p docs/frontend/reference
cp -R frontend/dist/docs/reference/. docs/frontend/reference/
PYTHONPATH=backend/src:intelligence-system/src uv run --project docs mkdocs serve
```

Default local MkDocs URL: http://127.0.0.1:8000

### GitHub docs publication

Docs workflow publishes to GitHub Pages from `.github/workflows/docs.yml`.

URL:

- https://<github_username>.github.io/ada502-fireguard-project/

If not available, ensure GitHub Pages is enabled in repo settings.

### In-cluster docs publication

Docs container is exposed at `/docs` through ingress:

- https://group10.ada502-fireguard.live/docs/

## CI/CD Workflows

### 1) Main CI pipeline

File: `.github/workflows/ci.yml`

Runs on push/PR to `main`:

- Secret scanning (`gitleaks`)
- Backend checks: lint, tests, Bandit, Docker build, Trivy
- Intelligence checks: lint, tests, Bandit, Docker build, Trivy
- Frontend checks: lint, typecheck, build, npm audit, Docker build, Trivy
- DAST baseline scan with OWASP ZAP

Deploy job (push to `main` only):

- SSH to NREC host
- `git pull`
- `kubectl apply -f k8s-manifests/`
- Restart deployments: backend, frontend, intelligence, docs
- Wait for rollout status
- Print ingress + docs pod status

### 2) Docker image publishing

File: `.github/workflows/docker-publish.yml`

On push to `main`:

- Builds and pushes images to GHCR:
  - `ghcr.io/<repo>-backend:latest`
  - `ghcr.io/<repo>-frontend:latest`
  - `ghcr.io/<repo>-intelligence:latest`
  - `ghcr.io/<repo>-docs:latest` (non-blocking)

### 3) Docs publishing

File: `.github/workflows/docs.yml`

On push to `main`:

- Runs TypeDoc for frontend API
- Syncs generated frontend docs into `docs/frontend/reference/`
- Builds MkDocs site
- Publishes to GitHub Pages when build artifact exists
- Uses non-blocking docs behavior to avoid blocking app delivery

## NREC Deployment Notes

Current NREC deployment target is Kubernetes exposed at:

- https://group10.ada502-fireguard.live/

Operational behavior:

- Deploy job applies manifests on host and restarts workloads.
- Deployments use `imagePullPolicy: Always` for app images.
- Image publishing (`docker-publish.yml`) and Kubernetes deploy (`ci.yml`) are separate workflows on `main`.
  If deploy finishes before fresh images are pushed, rerun deploy (or rollout restart) once image publishing completes.
- Ingress routes:
  - `/` -> frontend service
  - `/api` -> backend
  - `/auth` -> keycloak
  - `/mqtt` -> HiveMQ websocket endpoint
  - `/docs` -> docs service

If deployment succeeded but `/docs` is unavailable, run:

```bash
kubectl get ingress fireguard-ingress -o wide
kubectl get svc docs
kubectl get pods -l app=docs
kubectl describe pod -l app=docs
kubectl logs deployment/docs
```

## How to Verify a Fresh Deploy

After merge to `main`:

1. Check Actions:
   - CI workflow completed
   - Docker publish workflow completed
2. Check cluster rollout:

```bash
kubectl rollout status deployment/backend
kubectl rollout status deployment/frontend
kubectl rollout status deployment/intelligence
kubectl rollout status deployment/docs
```

3. Open live URLs:
   - https://group10.ada502-fireguard.live/
   - https://group10.ada502-fireguard.live/docs/

## Security and Secret Handling

- Do not commit real API keys/tokens in `.env`, ConfigMaps, or markdown.
- Store production credentials in:
  - GitHub Secrets/Variables (for workflows)
  - Kubernetes secrets (`fireguard-secrets`) on target clusters
- Rotate ThingSpeak and MQTT credentials if they were ever committed publicly.

## Troubleshooting Quick Reference

- API reachable, UI broken:
  - verify `VITE_API_URL` and frontend build args
- Login fails:
  - verify realm import, `frontend-client`, redirect URIs, and `/auth` ingress path
- MQTT alerts missing:
  - verify HiveMQ auth credentials and websocket route `/mqtt`
- ThingSpeak graph empty:
  - verify `THINGSPEAK_CHANNEL_ID`, write/read keys, and backend worker logs
- Docs 404/unreachable on cluster:
  - verify docs deployment/service/ingress and docs image pull status

## Useful Commands

```bash
# Local full stack
docker compose up --build

# Rebuild frontend docs and MkDocs locally
npm --prefix frontend run docs:api
mkdir -p docs/frontend/reference
cp -R frontend/dist/docs/reference/. docs/frontend/reference/
PYTHONPATH=backend/src:intelligence-system/src uv run --project docs mkdocs build

# Re-apply cluster manifests
kubectl apply -f k8s-manifests/

# Force pull latest images by restarting deployments
kubectl rollout restart deployment/backend deployment/frontend deployment/intelligence deployment/docs
```
