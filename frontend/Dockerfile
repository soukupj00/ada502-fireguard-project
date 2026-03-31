# STAGE 1: Base (Used by both Dev and Prod)
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
# Use 'npm ci' for reliable installs
RUN npm ci

# STAGE 2: Development (Target this for local dev)
FROM base AS development
COPY . .
EXPOSE 5173
# Expose the host flag so it binds to 0.0.0.0
CMD ["npm", "run", "dev", "--", "--host"]

# STAGE 3: Build (Intermediate step for Prod)
FROM base AS builder

# Define build arguments that will be passed from docker-compose.prod.yml
ARG VITE_API_URL
ARG VITE_KEYCLOAK_URL
ARG VITE_MQTT_BROKER_URL
ARG VITE_THINGSPEAK_CHANNEL_ID
ARG VITE_THINGSPEAK_READ_API_KEY

# Set them as environment variables so Vite can embed them during the build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_MQTT_BROKER_URL=$VITE_MQTT_BROKER_URL
ENV VITE_THINGSPEAK_CHANNEL_ID=$VITE_THINGSPEAK_CHANNEL_ID
ENV VITE_THINGSPEAK_READ_API_KEY=$VITE_THINGSPEAK_READ_API_KEY

COPY . .
RUN npm run build

# STAGE 4: Production (Target this for NREC/Prod)
FROM nginx:alpine AS production

# Force Alpine to patch the zlib vulnerability Trivy caught
RUN apk update && apk upgrade --no-cache zlib

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy custom Nginx config
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
