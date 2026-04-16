import { MapView } from "@/components/map/map-view"
import { SelectionMap } from "@/components/map/selection-map"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState, useMemo } from "react"
import {
  MapPin,
  MousePointerClick,
  PanelRightClose,
  PanelRightOpen,
} from "lucide-react"
import { useZones } from "@/hooks/use-zones"
import { useSubscriptions } from "@/hooks/use-subscriptions"
import Geohash from "latlon-geohash"
import type { MapFeature } from "@/types/map"
import { HistoryWidget } from "@/components/HistoryWidget"
import { RiskLegendWidget } from "@/components/RiskLegendWidget"
import { SubscriptionPanel } from "@/components/SubscriptionPanel"
import { useMqttAlerts } from "@/hooks/use-mqtt-alerts"
import { AnalyticsWidget } from "@/components/AnalyticsWidget"

export default function DashboardPage() {
  const [isSelectionMode, setIsSelectionMode] = useState(false)
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number
    lng: number
  } | null>(null)

  // Panel is open by default
  const [isPanelOpen, setIsPanelOpen] = useState(true)

  const handleLocationSelect = (lat: number, lng: number) => {
    setSelectedLocation({ lat, lng })
    setIsSelectionMode(false)
  }

  // Dashboard fetches BOTH regional zones and user subscriptions
  const {
    zones: regionalZones,
    isLoading: isRegionalLoading,
    isError: isRegionalError,
  } = useZones(true)
  const {
    geohashes: subscribedGeohashes,
    isLoading: isSubsLoading,
    isError: isSubsError,
  } = useSubscriptions()

  const mapFeatures = useMemo(() => {
    const combinedFeatures: MapFeature[] = []

    if (regionalZones?.features) {
      regionalZones.features.forEach((feature) => {
        const { geohash, risk_score, name, risk_category } = feature.properties
        if (!geohash || risk_score === null) return

        try {
          const bounds = Geohash.bounds(geohash)
          combinedFeatures.push({
            id: `regional-${geohash}`,
            name: name || `Regional Zone ${geohash}`,
            bounds: [
              [bounds.sw.lat, bounds.sw.lon],
              [bounds.ne.lat, bounds.ne.lon],
            ],
            riskScore: risk_score,
            riskCategory: risk_category ?? "N/A",
            isRegional: true,
          })
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (e) {
          // ignore invalid geohash
        }
      })
    }

    if (subscribedGeohashes?.length) {
      subscribedGeohashes.forEach((geohash) => {
        try {
          const bounds = Geohash.bounds(geohash)

          combinedFeatures.push({
            id: `sub-${geohash}`,
            name: `User Subscription ${geohash}`,
            bounds: [
              [bounds.sw.lat, bounds.sw.lon],
              [bounds.ne.lat, bounds.ne.lon],
            ],
            riskScore: 0,
            riskCategory: "N/A",
            isRegional: false,
          })
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (e) {
          // ignore invalid geohash
        }
      })
    }

    return combinedFeatures
  }, [regionalZones, subscribedGeohashes])

  // Activate MQTT alerts based on the user's subscriptions
  useMqttAlerts(mapFeatures.filter((f) => !f.isRegional))

  return (
    <div className="container mx-auto flex-1 p-4 py-8">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="mb-2 text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">
            Manage your monitored zones and analyze specific fire risks.
          </p>
        </div>

        <Button
          variant="outline"
          className="shrink-0 gap-2"
          onClick={() => setIsPanelOpen(!isPanelOpen)}
        >
          {isPanelOpen ? (
            <PanelRightClose className="h-4 w-4" />
          ) : (
            <PanelRightOpen className="h-4 w-4" />
          )}
          Manage Subscriptions
        </Button>
      </div>

      <div className="flex flex-col items-start lg:flex-row">
        <div className="w-full min-w-0 flex-1 transition-all duration-300 ease-in-out">
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
                onClick={() => {
                  setIsSelectionMode(!isSelectionMode)
                  // If we are cancelling selection mode, clear the selected location
                  if (isSelectionMode) {
                    setSelectedLocation(null)
                  }
                  // If opening selection mode and panel is closed, open it so user sees the form
                  if (!isSelectionMode && !isPanelOpen) {
                    setIsPanelOpen(true)
                  }
                }}
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
            <CardContent className="relative flex min-h-[400px] flex-1 flex-col p-0">
              {isSelectionMode ? (
                <div className="min-h-[400px] flex-1">
                  <SelectionMap
                    selectedLocation={selectedLocation}
                    onLocationSelect={handleLocationSelect}
                  />
                </div>
              ) : (
                <div className="min-h-[400px] flex-1">
                  <MapView
                    features={mapFeatures}
                    isLoading={isRegionalLoading || isSubsLoading}
                    isError={isRegionalError || isSubsError}
                    autoZoomToBounds={true}
                    selectedLocation={selectedLocation}
                  />
                </div>
              )}
              <div className="border-t bg-muted/10 p-4">
                <RiskLegendWidget legend={regionalZones?.risk_legend} />
              </div>
            </CardContent>
          </Card>
        </div>

        <div
          className={`shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${
            isPanelOpen
              ? "mt-8 w-full opacity-100 lg:mt-0 lg:ml-8 lg:w-[400px]"
              : "m-0 h-0 w-0 opacity-0 lg:h-auto"
          }`}
        >
          <div className="w-full lg:w-[400px]">
            <SubscriptionPanel
              isSelectionMode={isSelectionMode}
              selectedLocation={selectedLocation}
              onEditLocation={() => setIsSelectionMode(true)}
              onSubscriptionSuccess={() => {
                setIsSelectionMode(false)
                setSelectedLocation(null)
              }}
            />
          </div>
        </div>
      </div>

      <div className="mt-8">
        <AnalyticsWidget />
        <HistoryWidget />
      </div>
    </div>
  )
}
