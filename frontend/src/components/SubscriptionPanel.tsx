import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LocationSubscriber } from "@/components/LocationSubscriber"
import RiskAlertsWidget from "@/components/RiskAlertsWidget"
import { cn } from "@/lib/utils"

interface SubscriptionPanelProps {
  isSelectionMode: boolean
  selectedLocation: { lat: number; lng: number } | null
  onEditLocation: () => void
  onSubscriptionSuccess: () => void
}

export function SubscriptionPanel({
  isSelectionMode,
  selectedLocation,
  onEditLocation,
  onSubscriptionSuccess,
}: SubscriptionPanelProps) {
  return (
    <div className="flex flex-col gap-8">
      <Card
        className={cn(
          "shadow-sm transition-all duration-300",
          selectedLocation
            ? "border-primary ring-2 ring-primary ring-inset"
            : ""
        )}
      >
        <CardHeader className="pb-4">
          <CardTitle>Subscribe to Area</CardTitle>
          <CardDescription>
            {selectedLocation
              ? isSelectionMode
                ? "Pick a location on the map, then continue subscribing here"
                : "Location selected. Review it here or choose a different one."
              : "Click 'Select Area' on the map to pick a new location"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {selectedLocation && !isSelectionMode && (
            <div className="mb-4 flex items-center justify-between rounded-md border bg-muted/20 px-3 py-2 text-sm">
              <div>
                <span className="font-medium">Selected location:</span>{" "}
                <span className="font-mono text-muted-foreground">
                  {selectedLocation.lat.toFixed(5)},{" "}
                  {selectedLocation.lng.toFixed(5)}
                </span>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onEditLocation}
              >
                Change location
              </Button>
            </div>
          )}
          <LocationSubscriber
            selectedLat={selectedLocation?.lat ?? null}
            selectedLon={selectedLocation?.lng ?? null}
            onSuccess={onSubscriptionSuccess}
          />
        </CardContent>
      </Card>

      <Card className="flex-1 shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle>My Subscriptions</CardTitle>
          <CardDescription>
            Manage your personalized risk alerts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RiskAlertsWidget />
        </CardContent>
      </Card>
    </div>
  )
}
