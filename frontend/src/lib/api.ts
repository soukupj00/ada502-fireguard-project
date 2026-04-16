/**
 * HTTP client for authenticated API requests to the FastAPI backend.
 *
 * Provides typed fetch wrappers that automatically handle:
 * - Keycloak JWT token injection and refresh
 * - API endpoint URL normalization
 * - Error message extraction from responses
 * - JSON serialization/deserialization
 *
 * All functions include Bearer token authentication if user is authenticated.
 *
 * @module lib/api
 */

import keycloak from "../keycloak"
import { API_URL } from "./env"
import type {
  GeoJSONResponse,
  SubscriptionRequest,
  SubscriptionResponse,
  FireRiskReading,
} from "./types"

/**
 * FastAPI backend API version prefix for all endpoints.
 * @type {string}
 */
const API_VERSION = "/api/v1"

/**
 * FastAPI backend base URL (normalized without trailing slash).
 * @type {string}
 */
const API_BASE_URL = API_URL.replace(/\/$/, "")

/**
 * Tests if a URL string is absolute (starts with http:// or https://).
 *
 * @param {string} value - URL to test
 * @returns {boolean} True if URL is absolute
 */
const isAbsoluteUrl = (value: string) => /^https?:\/\//i.test(value)

/**
 * Normalizes endpoint paths to include API version prefix.
 *
 * Handles:
 * - Absolute URLs (returned unchanged)
 * - Relative paths without leading slash (adds /)
 * - Paths already prefixed with /api/v1 (returned unchanged)
 *
 * @param {string} endpoint - Endpoint path (e.g., "/zones", "zones")
 * @returns {string} Normalized endpoint with /api/v1 prefix
 */
const normalizeEndpoint = (endpoint: string) => {
  if (isAbsoluteUrl(endpoint)) {
    return endpoint
  }

  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  return path.startsWith(API_VERSION) ? path : `${API_VERSION}${path}`
}

/**
 * Builds a complete API URL from endpoint path.
 *
 * Combines base URL with normalized endpoint, handling both relative
 * and absolute URLs.
 *
 * @param {string} endpoint - Endpoint path or full URL
 * @returns {string} Complete API URL
 */
export const buildApiUrl = (endpoint: string) => {
  if (isAbsoluteUrl(endpoint)) {
    return endpoint
  }

  return `${API_BASE_URL}${normalizeEndpoint(endpoint)}`
}

/**
 * Extracts user-friendly error message from API response.
 *
 * Attempts to parse JSON for `detail` or `message` fields,
 * falls back to plain text or HTTP status code.
 *
 * @async
 * @param {Response} response - HTTP response object
 * @returns {Promise<string>} Error message suitable for display
 */
const getErrorMessage = async (response: Response) => {
  const fallback = `HTTP error! status: ${response.status}`

  try {
    const text = await response.text()
    if (!text) return fallback

    const payload = JSON.parse(text) as
      | { detail?: string; message?: string }
      | string

    if (typeof payload === "string") {
      return payload
    }

    return payload.detail ?? payload.message ?? text ?? fallback
  } catch {
    return fallback
  }
}

/**
 * Fetches from authenticated API endpoint with Keycloak JWT.
 *
 * Automatically:
 * - Injects Keycloak JWT in Authorization header
 * - Refreshes token if expiring within 30 seconds
 * - Redirects to login if token refresh fails
 * - Throws error with API message on 4xx/5xx status
 *
 * @async
 * @param {string} endpoint - API endpoint path (e.g., "/zones", "zones")
 * @param {RequestInit} [options={}] - Fetch options (method, body, headers, etc.)
 * @returns {Promise<Response>} HTTP response object
 * @throws {Error} If authentication fails or API returns error status
 */
export const fetchWithAuth = async (
  endpoint: string,
  options: RequestInit = {}
) => {
  const headers = new Headers(options.headers)

  if (keycloak.authenticated) {
    try {
      await keycloak.updateToken(30)
      headers.set("Authorization", `Bearer ${keycloak.token}`)
    } catch (error) {
      console.error("Failed to refresh token", error)
      await keycloak.login()
      throw new Error("Authentication required")
    }
  }

  const fetchOptions: RequestInit = {
    ...options,
    headers,
    credentials: options.credentials ?? "include",
  }

  const url = buildApiUrl(endpoint)

  const response = await fetch(url, fetchOptions)

  if (!response.ok) {
    throw new Error(await getErrorMessage(response))
  }

  return response
}

/**
 * Generic JSON API fetch with automatic authentication.
 *
 * Typed wrapper around fetchWithAuth that parses response as JSON.
 * Handles 204 No Content responses by returning undefined.
 *
 * @async
 * @template T - Expected JSON response type
 * @param {string} endpoint - API endpoint path
 * @param {RequestInit} [options={}] - Fetch options
 * @returns {Promise<T>} Parsed JSON response
 * @throws {Error} If fetch or JSON parsing fails
 */
export const fetchJson = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const response = await fetchWithAuth(endpoint, options)

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

/**
 * Fetches monitored fire risk zones from the backend.
 *
 * Returns GeoJSON FeatureCollection of Zone objects with current risk data.
 *
 * @async
 * @param {boolean} [regionalOnly=true] - If true, only returns regional zones (excludes local monitoring)
 * @returns {Promise<GeoJSONResponse>} GeoJSON FeatureCollection of zones with fire risk
 */
export async function fetchZones(
  regionalOnly: boolean = true
): Promise<GeoJSONResponse> {
  return fetchJson<GeoJSONResponse>(`/zones/?regional_only=${regionalOnly}`)
}

/**
 * Fetches historical fire risk readings for specified zones and date range.
 *
 * @async
 * @param {string} [startDate] - ISO 8601 start date (optional)
 * @param {string} [endDate] - ISO 8601 end date (optional)
 * @param {string} [geohashes] - Comma-separated geohashes to filter (optional)
 * @returns {Promise<FireRiskReading[]>} Array of historical risk readings
 */
export const fetchHistory = async (
  startDate?: string,
  endDate?: string,
  geohashes?: string
): Promise<FireRiskReading[]> => {
  const params = new URLSearchParams()
  if (startDate) params.append("start_date", startDate)
  if (endDate) params.append("end_date", endDate)
  if (geohashes) params.append("geohashes", geohashes)

  const query = params.toString()
  return fetchJson<FireRiskReading[]>(`/history/${query ? `?${query}` : ""}`)
}

/**
 * Fetches data from secured endpoints requiring authentication.
 *
 * @async
 * @template T - Expected JSON response type
 * @param {string} endpoint - API endpoint path
 * @returns {Promise<T>} Parsed JSON response
 */
export const fetchSecureData = async <T>(endpoint: string) => {
  return fetchJson<T>(endpoint)
}

/**
 * Subscribes current user to fire risk alerts for a zone.
 *
 * Creates subscription to receive notifications when fire risk exceeds
 * configured threshold in the specified geohash zone.
 *
 * @async
 * @param {SubscriptionRequest} payload - Subscription request with geohash
 * @returns {Promise<SubscriptionResponse>} Subscription confirmation and status
 */
export const subscribeToLocation = async (
  payload: SubscriptionRequest
): Promise<SubscriptionResponse> => {
  const requestBody =
    typeof payload === "string" ? { geohash: payload } : payload

  return fetchJson<SubscriptionResponse>("/users/me/subscriptions/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  })
}

/**
 * Cancels user subscription to fire risk alerts for a zone.
 *
 * Removes subscription, stopping alert notifications for the zone.
 *
 * @async
 * @param {string} geohash - Geohash of zone to unsubscribe from
 * @returns {Promise<void>}
 */
export const deleteSubscription = async (geohash: string): Promise<void> => {
  await fetchWithAuth(
    `/users/me/subscriptions/${encodeURIComponent(geohash)}/`,
    {
      method: "DELETE",
    }
  )
}
