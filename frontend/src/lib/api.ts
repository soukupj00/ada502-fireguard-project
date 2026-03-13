import type { GeoJSONResponse } from "./types"

// Use localhost for development, can be configured via environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export async function fetchZones(
  regionalOnly: boolean = true
): Promise<GeoJSONResponse> {
  const response = await fetch(
    `${API_BASE_URL}/zones/?regional_only=${regionalOnly}`
  )
  if (!response.ok) {
    throw new Error("Failed to fetch zones")
  }
  return response.json()
}
