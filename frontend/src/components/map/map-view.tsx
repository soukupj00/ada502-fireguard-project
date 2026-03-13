import { MapContainer, Popup, Rectangle, TileLayer } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import type { LatLngBoundsExpression, LatLngExpression } from "leaflet"
import { useZones } from "@/hooks/use-zones"
import { useMemo } from "react"
import Geohash from "latlon-geohash"
import type { MapFeature, SkippedFeature } from "@/types/map"

interface MapViewProps {
  center?: LatLngExpression
  zoom?: number
}

export function MapView({
  center = [58.359375, 10.546875] as LatLngExpression,
  zoom = 6,
}: MapViewProps) {
  const { zones, isLoading, isError } = useZones()

  const getColor = (riskScore: number) => {
    if (riskScore >= 80) return "#ef4444" // red-500
    if (riskScore >= 50) return "#f97316" // orange-500
    if (riskScore >= 20) return "#eab308" // yellow-500
    return "#22c55e" // green-500
  }

  const mapData = useMemo(() => {
    if (!zones) return []

    console.group("Map Data Debug")
    console.log("Total features:", zones.features.length)

    const skippedFeatures: SkippedFeature[] = []

    const processedData = zones.features
      .map((feature, index): MapFeature | null => {
        const { geohash, risk_score, name, risk_category } = feature.properties

        // Skip if geohash is missing or if risk_score is null (sea/no data)
        if (!geohash || risk_score === null) {
          skippedFeatures.push({
            index,
            reason: !geohash ? "Missing geohash" : "Null risk_score",
            feature: feature.properties,
          })

          if (!geohash)
            console.warn(`Feature at index ${index} missing geohash`, feature)
          return null
        }

        try {
          const bounds = Geohash.bounds(geohash)

          const leafletBounds: LatLngBoundsExpression = [
            [bounds.sw.lat, bounds.sw.lon],
            [bounds.ne.lat, bounds.ne.lon],
          ]

          return {
            id: geohash,
            name,
            bounds: leafletBounds,
            riskScore: risk_score,
            riskCategory: risk_category ?? "N/A",
          }
        } catch (e) {
          console.error(`Invalid geohash: ${geohash}`, e)
          return null
        }
      })
      .filter((item): item is MapFeature => item !== null)

    if (skippedFeatures.length > 0) {
      console.groupCollapsed(`Skipped Features (${skippedFeatures.length})`)
      console.table(skippedFeatures)
      console.groupEnd()
    }

    console.log("Processed map data:", processedData)
    console.groupEnd()

    return processedData
  }, [zones])

  if (isLoading) {
    return (
      <div className="flex h-full min-h-100 w-full animate-pulse items-center justify-center bg-muted/20">
        <span className="font-medium text-muted-foreground">
          Loading map data...
        </span>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex h-full min-h-100 w-full flex-col items-center justify-center bg-red-50 p-4 text-center text-red-500">
        <p className="font-bold">Error loading map data</p>
        <p className="text-sm">Please try again later.</p>
      </div>
    )
  }

  return (
    <div className="relative z-0 h-full w-full">
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        style={{ height: "100%", width: "100%", minHeight: "400px" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {mapData.map((data) => (
          <Rectangle
            key={data.id}
            bounds={data.bounds}
            pathOptions={{
              color: getColor(data.riskScore),
              fillColor: getColor(data.riskScore),
              fillOpacity: 0.5,
              weight: 1,
              stroke: false, // Remove stroke to make gaps less visible if they are caused by border width
            }}
          >
            <Popup>
              <div className="min-w-37.5 p-1 text-sm">
                <h3 className="mb-2 text-base font-semibold">{data.name}</h3>
                <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
                  <span className="font-medium text-muted-foreground">
                    Geohash:
                  </span>
                  <span className="text-right font-mono">{data.id}</span>

                  <span className="font-medium text-muted-foreground">
                    Risk Score:
                  </span>
                  <span
                    className={`text-right font-bold ${data.riskScore > 50 ? "text-red-600" : "text-green-600"}`}
                  >
                    {data.riskScore.toFixed(1)}
                  </span>

                  <span className="font-medium text-muted-foreground">
                    Category:
                  </span>
                  <span className="text-right capitalize">
                    {data.riskCategory}
                  </span>
                </div>
              </div>
            </Popup>
          </Rectangle>
        ))}
      </MapContainer>
    </div>
  )
}
