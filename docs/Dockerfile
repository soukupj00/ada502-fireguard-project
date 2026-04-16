FROM node:20-alpine AS frontend-docs
WORKDIR /repo/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run docs:api

FROM python:3.12-alpine AS docs-builder
WORKDIR /repo
# Install build dependencies for compiling pygeohash and other packages
RUN apk add --no-cache gcc musl-dev python3-dev
COPY docs/pyproject.toml docs/pyproject.toml
RUN pip install --no-cache-dir uv
RUN uv sync --project docs
COPY mkdocs.yml ./
COPY docs ./docs
COPY backend ./backend
COPY intelligence-system ./intelligence-system
RUN mkdir -p docs/frontend/reference
COPY --from=frontend-docs /repo/frontend/dist/docs/reference/. ./docs/frontend/reference/
RUN PYTHONPATH=backend/src:intelligence-system/src uv run --project docs mkdocs build

FROM nginx:1.27-alpine
COPY docs/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=docs-builder /repo/site /usr/share/nginx/html
