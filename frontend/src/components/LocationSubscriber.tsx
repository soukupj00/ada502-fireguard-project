import { useState, useEffect } from "react"
import { useSWRConfig } from "swr"
import Geohash from "latlon-geohash"

import { Loader2, MapPin } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { subscribeToLocation } from "@/lib/api"
import { useLocationStream } from "@/hooks/use-location-stream"
import { toast } from "sonner"

interface LocationSubscriberProps {
  selectedLat?: number | null
  selectedLon?: number | null
  onSuccess?: () => void
}

export function LocationSubscriber({
  selectedLat = null,
  selectedLon = null,
  onSuccess,
}: LocationSubscriberProps) {
  const [geohash, setGeohash] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [pendingGeohash, setPendingGeohash] = useState<string | null>(null)
  const { mutate } = useSWRConfig()

  // Subscribe to the SSE stream if we are waiting for a new location
  const { riskData, error } = useLocationStream(pendingGeohash)

  useEffect(() => {
    if (selectedLat === null || selectedLon === null) return
    // Precision 5 keeps subscriptions at a practical area size.
    setGeohash(Geohash.encode(selectedLat, selectedLon, 5))
  }, [selectedLat, selectedLon])

  useEffect(() => {
    if (riskData) {
      toast.info("Real-time risk data received!", {
        description: `Risk Level: ${riskData.risk_category} (Score: ${riskData.risk_score?.toFixed(2)})`,
      })
      // Clear pending geohash once data is received
      setPendingGeohash(null)
      // Re-fetch zones to show on map
      mutate(["/zones", false])
      mutate("/users/me/subscriptions/")
      // Call success callback to clear selection and clean up UI
      onSuccess?.()
    }
  }, [riskData, mutate, onSuccess])

  useEffect(() => {
    if (error) {
      toast.error("Stream Error", {
        description:
          "Failed to receive real-time updates for the new location.",
      })
      console.error("SSE Error:", error)
      setPendingGeohash(null)
    }
  }, [error])

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!geohash.trim()) return

    setIsSubmitting(true)
    try {
      const response = await subscribeToLocation(geohash)

      if (response.status === "active") {
        toast.success("Successfully subscribed to location")
        mutate(["/zones", false])
        mutate("/users/me/subscriptions/")
        onSuccess?.()
      } else if (response.status === "pending") {
        toast.info(
          "Subscription queued. Waiting for initial risk calculation..."
        )
        // Start listening to the SSE stream
        setPendingGeohash(response.geohash)
      }
      setGeohash("")
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "An unexpected error occurred."
      toast.error("Failed to subscribe", {
        description: errorMessage,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Subscribe to a Location</CardTitle>
        <CardDescription>
          Enter a Geohash to receive real-time fire risk alerts for that area.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubscribe} className="flex space-x-2">
          <Input
            type="text"
            placeholder="e.g. u4pru"
            value={geohash}
            onChange={(e) => setGeohash(e.target.value)}
            disabled={isSubmitting || pendingGeohash !== null}
            required
            className="font-mono lowercase"
          />
          <Button
            type="submit"
            disabled={isSubmitting || pendingGeohash !== null}
          >
            {isSubmitting || pendingGeohash ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <MapPin className="mr-2 h-4 w-4" />
            )}
            {pendingGeohash ? "Calculating..." : "Subscribe"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
