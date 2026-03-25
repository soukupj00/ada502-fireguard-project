import useSWRSubscription from "swr/subscription"
import keycloak from "@/keycloak"
import type { FireRiskReading } from "@/lib/types"

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"
const API_VERSION = "/api/v1"

export function useLocationStream(geohash: string | null) {
  // Update path to /users/me/subscriptions/{geohash}/stream instead of /zones/{geohash}/stream
  const key = geohash
    ? `${API_BASE_URL}${API_VERSION}/users/me/subscriptions/${geohash}/stream`
    : null

  const { data, error } = useSWRSubscription(
    key,
    (
      url: string,
      {
        next,
      }: { next: (err: Error | null, data?: FireRiskReading | null) => void }
    ) => {
      // SSE requires authorization if the endpoint is protected
      // However, Standard EventSource doesn't support custom headers (like Authorization)
      // We can use a query parameter for the token if the backend supports it,
      // or just assume it's public/handled via cookies if possible.
      // Given the task, I will stick to the provided example but adapt to our project.

      // If we need to pass a token, we might need a library like `event-source-polyfill` or
      // include it in the URL if the backend accepts it.
      const eventSourceUrl = keycloak.token
        ? `${url}?token=${keycloak.token}`
        : url
      const eventSource = new EventSource(eventSourceUrl)

      eventSource.onmessage = (event) => {
        try {
          const riskData: FireRiskReading = JSON.parse(event.data)
          next(null, riskData)
          eventSource.close()
        } catch (err) {
          next(
            err instanceof Error
              ? err
              : new Error("Failed to parse stream data"),
            null
          )
          eventSource.close()
        }
      }

      eventSource.onerror = (err: Event) => {
        next(new Error(`EventSource error occurred: ${err}`), null)
        eventSource.close()
      }

      return () => eventSource.close()
    }
  )

  return { riskData: data, error }
}
