/**
 * React hook for fetching historical sensor data from ThingSpeak.
 *
 * Retrieves time-series temperature and humidity data for correlation
 * with fire risk metrics. Requires ThingSpeak Channel ID and optional API key.
 *
 * @module hooks/use-thingspeak-data
 */

/**
 * React hook for fetching historical sensor data from ThingSpeak.
 *
 * Retrieves time-series temperature and humidity data for correlation with fire risk metrics.
 * Requires ThingSpeak Channel ID and optional API key in environment variables.
 *
 * @module hooks/use-thingspeak-data
 */

import useSWR from "swr"
import { THINGSPEAK_CHANNEL_ID, THINGSPEAK_READ_API_KEY } from "@/lib/env"
import type { ThingSpeakResponse } from "@/types/thingspeak"

/**
 * Fetcher function for ThingSpeak API requests.
 *
 * @async
 * @param {string} url - ThingSpeak API endpoint
 * @returns {Promise<ThingSpeakResponse>} Parsed API response
 * @throws {Error} If API call fails or returns error
 */
const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    const errorData = await res.json()
    throw new Error(errorData.message || "Failed to fetch ThingSpeak data")
  }
  return res.json()
}

/**
 * Hook for fetching time-series sensor data from ThingSpeak.
 *
 * Retrieves historical temperature and humidity readings for visualization
 * and fire risk correlation analysis. Returns null if ThingSpeak Channel ID
 * is not configured in environment variables.
 *
 * Auto-refreshes every 60 seconds (subject to ThingSpeak API rate limits).
 *
 * @param {number} [results=24] - Number of most recent readings to fetch
 * @returns {Object} Sensor data and control functions
 * @returns {ThingSpeakResponse} data - Time-series data from ThingSpeak
 * @returns {boolean} isLoading - Whether data is being fetched
 * @returns {Error} isError - Error if fetch fails or Channel ID is missing
 * @returns {Function} mutate - Manual cache invalidation/refresh function
 */
export function useThingspeakData(results: number = 24) {
  // Construct the ThingSpeak API URL only if the Channel ID is provided
  let urlStr: string | null = null

  if (THINGSPEAK_CHANNEL_ID) {
    const url = new URL(
      `https://api.thingspeak.com/channels/${THINGSPEAK_CHANNEL_ID}/feeds.json`
    )
    url.searchParams.append("results", results.toString())

    if (THINGSPEAK_READ_API_KEY) {
      url.searchParams.append("api_key", THINGSPEAK_READ_API_KEY)
    }
    urlStr = url.toString()
  }

  // Passing null as the URL to useSWR prevents it from fetching.
  // This satisfies the Rules of Hooks by ensuring useSWR is always called.
  const { data, error, isLoading, mutate } = useSWR<ThingSpeakResponse>(
    urlStr,
    fetcher,
    {
      refreshInterval: 60000, // Auto-refresh every 60 seconds (ThingSpeak rate limits apply)
    }
  )

  // Determine the final error state based on missing config or actual fetch error
  const finalError = !THINGSPEAK_CHANNEL_ID
    ? new Error(
        "ThingSpeak Channel ID is not configured in environment variables."
      )
    : error

  return {
    data,
    isLoading: isLoading && !!THINGSPEAK_CHANNEL_ID,
    isError: finalError,
    mutate,
  }
}
