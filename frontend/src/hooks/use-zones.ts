/**
 * React hook for fetching and managing fire risk zones.
 *
 * Retrieves monitored zones (regional or all) from the backend,
 * formatted as GeoJSON for map visualization. Data is cached with automatic hourly refresh.
 *
 * @module hooks/use-zones
 */

import useSWR from "swr"
import { fetchZones } from "@/lib/api"
import type { GeoJSONResponse } from "@/lib/types"

export function useZones(regionalOnly: boolean = true) {
  const { data, error, isLoading, mutate } = useSWR<GeoJSONResponse>(
    ["/zones", regionalOnly],
    () => fetchZones(regionalOnly),
    {
      refreshInterval: 60 * 60000, // Refresh every hour
      revalidateOnFocus: false,
    }
  )

  return {
    zones: data,
    isLoading,
    isError: error,
    mutate,
  }
}
