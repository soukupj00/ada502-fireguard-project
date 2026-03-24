import { fetchSecureData, deleteSubscription } from "@/lib/api"
import useSWR, { useSWRConfig } from "swr"
import type { ApiError, GeoJSONResponse } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Trash2 } from "lucide-react"
import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { toast } from "sonner"

export default function RiskAlertsWidget() {
  const { mutate } = useSWRConfig()
  const { data, error, isLoading } = useSWR<GeoJSONResponse>(
    "/users/me/subscriptions/",
    fetchSecureData
  )

  const [deletingGeohash, setDeletingGeohash] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  if (isLoading)
    return (
      <div className="text-sm text-muted-foreground">
        Loading subscriptions...
      </div>
    )
  if (error)
    return (
      <div className="text-sm text-red-500">Failed to load subscriptions</div>
    )

  const subscriptions = data?.features || []

  if (subscriptions.length === 0) {
    return (
      <div className="text-sm text-muted-foreground italic">
        No active subscriptions
      </div>
    )
  }

  const handleDelete = async () => {
    if (!deletingGeohash) return

    setIsDeleting(true)
    try {
      await deleteSubscription(deletingGeohash)
      toast.success("Subscription removed")

      // Refresh both the subscriptions list and the map
      mutate("/users/me/subscriptions/")
      mutate(["/zones", false])

      setDeletingGeohash(null)
    } catch (err: unknown) {
      const apiError = err as ApiError
      const message = apiError.message || "An unknown error occurred"
      const detail = apiError.response?.data?.detail

      toast.error("Failed to remove subscription", {
        description: detail || message,
      })
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      {subscriptions.map((sub) => {
        const { geohash, name, risk_score, risk_category } = sub.properties
        return (
          <div
            key={geohash}
            className="flex items-center justify-between rounded-md border p-4"
          >
            <div className="flex-1">
              <h4 className="font-semibold">{name || "Unnamed Area"}</h4>
              <p className="text-sm text-muted-foreground">
                Geohash: {geohash}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div
                className={`rounded-full px-3 py-1 text-sm font-bold ${
                  risk_score !== null && risk_score > 50
                    ? "bg-red-100 text-red-700"
                    : "bg-green-100 text-green-700"
                }`}
              >
                {risk_score !== null ? `Risk: ${risk_score}` : "N/A"}
                {risk_category && (
                  <span className="ml-1 opacity-70">({risk_category})</span>
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-destructive"
                onClick={() => setDeletingGeohash(geohash)}
              >
                <Trash2 className="h-4 w-4" />
                <span className="sr-only">Delete</span>
              </Button>
            </div>
          </div>
        )
      })}

      <Dialog
        open={!!deletingGeohash}
        onOpenChange={(open) => !open && setDeletingGeohash(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Subscription</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove your subscription for this area?
              You will no longer receive alerts for this location.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeletingGeohash(null)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={isDeleting}
            >
              {isDeleting ? "Removing..." : "Remove"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
