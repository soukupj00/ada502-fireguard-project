# STAGE 1: Base (Used by both Dev and Prod)
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

# STAGE 2: Development (Target this for local dev)
FROM base AS development
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

# STAGE 3: Build (Intermediate step for Prod)
FROM base AS builder

# Build args from docker-compose(.prod).yml
ARG VITE_API_URL
ARG VITE_KEYCLOAK_URL
ARG VITE_MQTT_BROKER_URL
ARG VITE_MQTT_USERNAME
ARG VITE_MQTT_PASSWORD
ARG VITE_THINGSPEAK_CHANNEL_ID
ARG VITE_THINGSPEAK_READ_API_KEY

# Expose args to Vite build
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_KEYCLOAK_URL=${VITE_KEYCLOAK_URL}
ENV VITE_MQTT_BROKER_URL=${VITE_MQTT_BROKER_URL}
ENV VITE_MQTT_USERNAME=${VITE_MQTT_USERNAME}
ENV VITE_MQTT_PASSWORD=${VITE_MQTT_PASSWORD}
ENV VITE_THINGSPEAK_CHANNEL_ID=${VITE_THINGSPEAK_CHANNEL_ID}
ENV VITE_THINGSPEAK_READ_API_KEY=${VITE_THINGSPEAK_READ_API_KEY}

COPY . .
RUN npm run build

# STAGE 4: Production
FROM nginx:alpine AS production

# Pull patched security packages from Alpine repos (fixes libpng CVEs reported by Trivy)
RUN apk --no-cache update && apk --no-cache upgrade

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
