import useSWR from "swr"
import { THINGSPEAK_CHANNEL_ID, THINGSPEAK_READ_API_KEY } from "@/lib/env"
import type { ThingSpeakResponse } from "@/types/thingspeak"

const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    const errorData = await res.json()
    throw new Error(errorData.message || "Failed to fetch ThingSpeak data")
  }
  return res.json()
}

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
