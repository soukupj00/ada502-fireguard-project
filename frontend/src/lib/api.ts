import keycloak from "../keycloak"
import { API_URL } from "./env"
import type {
  GeoJSONResponse,
  SubscriptionRequest,
  SubscriptionResponse,
  FireRiskReading,
} from "./types"

const API_VERSION = "/api/v1"
const API_BASE_URL = API_URL.replace(/\/$/, "")

const isAbsoluteUrl = (value: string) => /^https?:\/\//i.test(value)

const normalizeEndpoint = (endpoint: string) => {
  if (isAbsoluteUrl(endpoint)) {
    return endpoint
  }

  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  return path.startsWith(API_VERSION) ? path : `${API_VERSION}${path}`
}

export const buildApiUrl = (endpoint: string) => {
  if (isAbsoluteUrl(endpoint)) {
    return endpoint
  }

  return `${API_BASE_URL}${normalizeEndpoint(endpoint)}`
}

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

export async function fetchZones(
  regionalOnly: boolean = true
): Promise<GeoJSONResponse> {
  return fetchJson<GeoJSONResponse>(`/zones/?regional_only=${regionalOnly}`)
}

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

export const fetchSecureData = async <T>(endpoint: string) => {
  return fetchJson<T>(endpoint)
}

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

export const deleteSubscription = async (geohash: string): Promise<void> => {
  await fetchWithAuth(
    `/users/me/subscriptions/${encodeURIComponent(geohash)}/`,
    {
      method: "DELETE",
    }
  )
}
