import { useState } from "react"
import type { ApiError } from "@/lib/types"
import { subscribeToLocation } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import keycloak from "@/keycloak"
import { useSWRConfig } from "swr"

interface LocationSubscriberProps {
  selectedLat: number | null
  selectedLon: number | null
}

export function LocationSubscriber({
  selectedLat,
  selectedLon,
}: LocationSubscriberProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { mutate } = useSWRConfig()

  const handleSubscribe = async () => {
    // Safety check: is the user actually logged in?
    if (!keycloak.authenticated) {
      toast.error("Authentication Required", {
        description: "Please log in to subscribe to alerts.",
      })
      keycloak.login()
      return
    }

    if (selectedLat === null || selectedLon === null) return

    setIsSubmitting(true)
    try {
      const response = await subscribeToLocation({
        latitude: selectedLat,
        longitude: selectedLon,
      })

      // The backend returns a status: "active" (already tracked) or "pending" (new zone)
      toast.success("Subscription Successful!", {
        description: response.message || "You are now tracking this location.",
      })

      console.log("Subscribed Geohash:", response.geohash)

      // Re-fetch zones and user subscriptions to update map/list
      mutate(["/zones", false])
      mutate("/users/me/subscriptions/")
    } catch (error: unknown) {
      const apiError = error as ApiError
      const message = apiError.message || "An unknown error occurred"
      const detail = apiError.response?.data?.detail

      toast.error("Subscription Failed", {
        description: detail || message,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      {selectedLat !== null && selectedLon !== null ? (
        <p className="text-sm text-muted-foreground">
          Selected: {selectedLat.toFixed(4)}, {selectedLon.toFixed(4)}
        </p>
      ) : (
        <p className="text-sm text-muted-foreground">
          Select a location on the map to subscribe.
        </p>
      )}
      <Button
        onClick={handleSubscribe}
        disabled={isSubmitting || selectedLat === null || selectedLon === null}
      >
        {isSubmitting ? "Subscribing..." : "Subscribe to Alerts"}
      </Button>
    </div>
  )
}
