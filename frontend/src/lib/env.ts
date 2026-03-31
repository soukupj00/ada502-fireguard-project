// src/lib/env.ts

// --- MQTT Broker Configuration ---
// For development, this points to the local HiveMQ container's WebSocket port.
// For production, this should point to the Nginx proxy path (e.g., "wss://your-domain.com/mqtt").
export const MQTT_BROKER_URL =
  import.meta.env.VITE_MQTT_BROKER_URL || "ws://localhost:8000"

// --- ThingSpeak Configuration ---
// The public Channel ID for your ThingSpeak data.
export const THINGSPEAK_CHANNEL_ID =
  import.meta.env.VITE_THINGSPEAK_CHANNEL_ID || ""

// The Read API Key for your ThingSpeak channel.
// While some channels are public, it's good practice to use a Read API Key.
export const THINGSPEAK_READ_API_KEY =
  import.meta.env.VITE_THINGSPEAK_READ_API_KEY || ""

// --- API Configuration ---
// The base URL for your backend API.
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

// --- Keycloak Configuration ---
// The URL for your Keycloak authentication server.
export const KEYCLOAK_URL =
  import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080/auth"
export const KEYCLOAK_REALM =
  import.meta.env.VITE_KEYCLOAK_REALM || "fireguard-realm"
export const KEYCLOAK_CLIENT_ID =
  import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "fireguard-frontend"
