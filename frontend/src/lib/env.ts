/**
 * Environment variables and runtime configuration.
 *
 * Centralizes all environment-dependent configuration used in the frontend.
 * Configuration is loaded from Vite environment variables (VITE_ prefixed)
 * which are injected at build time.
 *
 * Includes:
 * - MQTT broker settings for real-time fire alerts
 * - ThingSpeak API credentials for sensor visualization
 * - Backend API endpoint
 * - Keycloak authentication server settings
 *
 * @module lib/env
 */

// --- MQTT Broker Configuration ---

/**
 * Raw MQTT broker URL from environment variables.
 * @type {string}
 */
const rawMqttBrokerUrl = import.meta.env.VITE_MQTT_BROKER_URL || "/mqtt"

/**
 * Converts relative paths to absolute WebSocket URLs.
 *
 * Automatically selects wss: for HTTPS origins and ws: for HTTP.
 * Used to handle dev/prod proxy differences transparently.
 *
 * @param {string} value - URL to resolve
 * @returns {string} Absolute WebSocket URL (ws:// or wss://)
 */
const resolveMqttUrl = (value: string) => {
  if (!value.startsWith("/")) {
    return value
  }

  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"
  return `${wsProtocol}//${window.location.host}${value}`
}

/**
 * MQTT broker WebSocket URL for real-time fire alerts.
 *
 * Used to connect to HiveMQ broker for receiving fire risk notifications
 * and zone updates in real-time.
 *
 * @type {string}
 */
export const MQTT_BROKER_URL = resolveMqttUrl(rawMqttBrokerUrl)

/**
 * MQTT broker username for authentication.
 * @type {string}
 */
export const MQTT_USERNAME = import.meta.env.VITE_MQTT_USERNAME || ""

/**
 * MQTT broker password for authentication.
 * @type {string}
 */
export const MQTT_PASSWORD = import.meta.env.VITE_MQTT_PASSWORD || ""

// --- ThingSpeak Configuration ---

/**
 * ThingSpeak channel ID for public sensor data.
 *
 * Used to fetch historical temperature and humidity data
 * for fire risk analysis visualization.
 *
 * @type {string}
 */
export const THINGSPEAK_CHANNEL_ID =
  import.meta.env.VITE_THINGSPEAK_CHANNEL_ID || ""

/**
 * ThingSpeak Read API Key for secure channel access.
 *
 * While ThingSpeak channels can be public, using an API key provides
 * better rate limiting and security guarantees.
 *
 * @type {string}
 */
export const THINGSPEAK_READ_API_KEY =
  import.meta.env.VITE_THINGSPEAK_READ_API_KEY || ""

// --- API Configuration ---

/**
 * Backend FastAPI server base URL.
 *
 * Can be absolute URL (for external APIs) or relative path
 * (for Nginx proxied access through reverse proxy).
 *
 * @type {string}
 */
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

// --- Keycloak Configuration ---

/**
 * Keycloak authentication server URL.
 *
 * OpenID Connect provider for user authentication and authorization.
 *
 * @type {string}
 */
export const KEYCLOAK_URL =
  import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080/auth"

/**
 * Keycloak realm name for FireGuard users and roles.
 *
 * Logical namespace isolating FireGuard users from other realms.
 *
 * @type {string}
 */
export const KEYCLOAK_REALM =
  import.meta.env.VITE_KEYCLOAK_REALM || "fireguard-realm"

/**
 * Keycloak client ID for OAuth2 authentication flow.
 *
 * Public client identifier registered in Keycloak realm.
 *
 * @type {string}
 */
export const KEYCLOAK_CLIENT_ID =
  import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "fireguard-frontend"
