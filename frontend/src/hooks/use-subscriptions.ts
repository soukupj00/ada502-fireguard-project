import useSWR from "swr"
import { fetchJson } from "@/lib/api"
import type { UserSubscriptionListResponse } from "@/lib/types"

const fetcher = (url: string) => fetchJson<UserSubscriptionListResponse>(url)

export function useSubscriptions() {
  const { data, error, isLoading, mutate } =
    useSWR<UserSubscriptionListResponse>("/users/me/subscriptions/", fetcher)

  return {
    subscriptions: data,
    geohashes: data?.geohashes ?? [],
    isLoading,
    isError: error,
    mutate,
  }
}
