import axios from "axios"
import keycloak from "../keycloak"
import type {
  GeoJSONResponse,
  SubscriptionRequest,
  SubscriptionResponse,
} from "./types"

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"
const API_VERSION = "/api/v1"

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_VERSION}`,
  // Add this line to ensure credentials/cookies are passed if needed by backend CORS
  withCredentials: true,
})

apiClient.interceptors.request.use(
  async (config) => {
    if (keycloak.authenticated) {
      try {
        await keycloak.updateToken(30)
        config.headers.Authorization = `Bearer ${keycloak.token}`
      } catch (error) {
        console.error("Failed to refresh token", error)
        keycloak.login()
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export async function fetchZones(
  regionalOnly: boolean = true
): Promise<GeoJSONResponse> {
  const response = await fetch(
    `${API_BASE_URL}${API_VERSION}/zones/?regional_only=${regionalOnly}`
  )
  if (!response.ok) {
    throw new Error("Failed to fetch zones")
  }
  return response.json()
}

export const fetchSecureData = async (endpoint: string) => {
  const response = await apiClient.get(endpoint)
  return response.data
}

export const subscribeToLocation = async (
  payload: SubscriptionRequest
): Promise<SubscriptionResponse> => {
  const response = await apiClient.post("/users/me/subscriptions/", payload)
  return response.data
}

export const deleteSubscription = async (geohash: string): Promise<void> => {
  await apiClient.delete(`/users/me/subscriptions/${geohash}`)
}
