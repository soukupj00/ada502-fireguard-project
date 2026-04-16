/**
 * FireGuard Frontend Public API and Type Exports.
 *
 * This module serves as the entry point for TypeDoc API documentation generation.
 * Exports all public-facing types and custom hooks that should be documented.
 *
 * Public exports include:
 * - Custom React hooks for fire risk monitoring and subscriptions
 * - TypeScript type definitions for API responses and domain entities
 * - Integration utilities for backend API and realt-time services
 *
 * @module frontend
 */

export * from "./lib/types"

/**
 * Hook for subscribing to real-time fire risk alerts via Server-Sent Events (SSE).
 *
 * Establishes a persistent connection to receive streaming risk data for a monitored zone.
 * Connection requires authentication and closes after first message.
 */
export { useLocationStream } from "./hooks/use-location-stream"

/**
 * Hook for receiving real-time fire risk alerts via MQTT WebSocket.
 *
 * Maintains connection to HiveMQ broker for published alerts about zones
 * exceeding risk thresholds. Auto-reconnects on disconnect.
 */
export { useMqttAlerts } from "./hooks/use-mqtt-alerts"

/**
 * Hook for managing user zone subscriptions and notifications.
 *
 * Provides functions to:
 * - Fetch user's active subscriptions
 * - Subscribe to new zones for alerts
 * - Unsubscribe from zones
 */
export { useSubscriptions } from "./hooks/use-subscriptions"

/**
 * Hook for fetching historical temperature and humidity data.
 *
 * Retrieves time-series sensor data from ThingSpeak API for visualization
 * and correlation with fire risk assessments.
 */
export { useThingspeakData } from "./hooks/use-thingspeak-data"

/**
 * Hook for managing monitored fire risk zones.
 *
 * Provides functions to:
 * - Fetch all monitored zones (regional or all)
 * - Format zones as GeoJSON for map visualization
 * - Track zone status and real-time risk levels
 */
export { useZones } from "./hooks/use-zones"
