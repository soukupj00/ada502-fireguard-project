import { MapView } from "@/components/map/map-view"
import { SelectionMap } from "@/components/map/selection-map"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import RiskAlertsWidget from "@/components/RiskAlertsWidget"
import { LocationSubscriber } from "@/components/LocationSubscriber"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { MapPin, MousePointerClick } from "lucide-react"

export default function DashboardPage() {
  const [isSelectionMode, setIsSelectionMode] = useState(false)
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number
    lng: number
  } | null>(null)

  const handleLocationSelect = (lat: number, lng: number) => {
    setSelectedLocation({ lat, lng })
  }

  return (
    <div className="container mx-auto flex-1 p-4 py-8">
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Manage your monitored zones and analyze specific fire risks.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        <div className="flex flex-col gap-8 lg:col-span-2">
          <Card className="flex h-full flex-col overflow-hidden border-muted/40 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <div>
                <CardTitle>
                  {isSelectionMode
                    ? "Select New Location"
                    : "Detailed Zone Map"}
                </CardTitle>
                <CardDescription>
                  {isSelectionMode
                    ? "Search or click on the map to drop a pin"
                    : "Zoomed in view of your tracked zones"}
                </CardDescription>
              </div>
              <Button
                variant={isSelectionMode ? "default" : "outline"}
                size="sm"
                onClick={() => setIsSelectionMode(!isSelectionMode)}
                className="gap-2"
              >
                {isSelectionMode ? (
                  <MapPin className="h-4 w-4" />
                ) : (
                  <MousePointerClick className="h-4 w-4" />
                )}
                {isSelectionMode ? "Cancel Selection" : "Select Area"}
              </Button>
            </CardHeader>
            <CardContent className="relative min-h-[500px] flex-1 p-0">
              {isSelectionMode ? (
                <SelectionMap
                  selectedLocation={selectedLocation}
                  onLocationSelect={handleLocationSelect}
                />
              ) : (
                <MapView />
              )}
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-8">
          <Card
            className={`shadow-sm transition-all duration-300 ${selectedLocation ? "border-primary ring-1 ring-primary" : ""}`}
          >
            <CardHeader className="pb-4">
              <CardTitle>Subscribe to Area</CardTitle>
              <CardDescription>
                {isSelectionMode
                  ? "Click the map to select coordinates"
                  : "Click 'Select Area' on the map to pick a new location"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LocationSubscriber
                selectedLat={selectedLocation?.lat ?? null}
                selectedLon={selectedLocation?.lng ?? null}
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
      </div>
    </div>
  )
}
