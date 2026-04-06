import {
  MapContainer,
  Popup,
  Rectangle,
  TileLayer,
  useMap,
  Marker,
} from "react-leaflet"
import "leaflet/dist/leaflet.css"
import type { LatLngBoundsExpression, LatLngExpression } from "leaflet"
import L from "leaflet"
import { useEffect, useMemo } from "react"
import { MapPatterns } from "./MapPatterns"
import { getRiskStyle } from "./map-styles"
import type { MapFeature } from "@/types/map"
import { MapResizer } from "./map-resizer"

interface MapViewProps {
  center?: LatLngExpression
  zoom?: number
  features: MapFeature[]
  isLoading?: boolean
  isError?: boolean
  autoZoomToBounds?: boolean
  selectedLocation?: { lat: number; lng: number } | null
}

function AutoZoom({
  bounds,
  selectedLocation,
}: {
  bounds: LatLngBoundsExpression | null
  selectedLocation: { lat: number; lng: number } | null
}) {
  const map = useMap()
  useEffect(() => {
    // If selected location exists, prioritize zooming to it closely
    if (selectedLocation) {
      map.setView([selectedLocation.lat, selectedLocation.lng], 10, {
        animate: true,
      })
    } else if (bounds) {
      // Otherwise use the bounds zoom if available
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 })
    }
  }, [bounds, selectedLocation, map])
  return null
}

export function MapView({
  center = [58.359375, 10.546875] as LatLngExpression,
  zoom = 6,
  features = [],
  isLoading = false,
  isError = false,
  autoZoomToBounds = false,
  selectedLocation = null,
}: MapViewProps) {
  // Sort: regional first, then user zones (so user zones are rendered on top)
  const sortedFeatures = useMemo(() => {
    return [...features].sort((a, b) => {
      if (a.isRegional === b.isRegional) return 0
      return a.isRegional ? -1 : 1
    })
  }, [features])

  // Optionally automatically zoom to bounds containing ALL user subscriptions
  const userZonesBounds = useMemo(() => {
    if (!autoZoomToBounds) return null

    const userZones = features.filter((f) => !f.isRegional)
    if (userZones.length === 0) return null

    const bounds = L.latLngBounds([])
    userZones.forEach((zone) => {
      bounds.extend(zone.bounds)
    })
    return bounds.isValid()
      ? (bounds as unknown as LatLngBoundsExpression)
      : null
  }, [features, autoZoomToBounds])

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
      <MapPatterns />
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        style={{ height: "100%", width: "100%", minHeight: "400px" }}
      >
        <MapResizer />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <AutoZoom
          bounds={userZonesBounds}
          selectedLocation={selectedLocation}
        />

        {sortedFeatures.map((data) => {
          const style = getRiskStyle(data.riskScore, data.isRegional)

          return (
            <Rectangle
              key={data.id}
              bounds={data.bounds}
              pathOptions={{
                color: style.color, // Border color
                fillColor:
                  style.pattern !== "none"
                    ? `url(#pattern-${style.pattern})`
                    : style.color, // Pattern or solid color
                fillOpacity: style.pattern !== "none" ? 1 : style.fillOpacity, // If pattern, use 1 so svg opacity works
                weight: style.weight, // Border thickness
                stroke: style.stroke, // Show border
                dashArray: style.dashArray,
              }}
            >
              <Popup>
                <div className="min-w-37.5 p-1 text-sm">
                  <h3 className="mb-2 text-base font-semibold">
                    {data.name}
                    {!data.isRegional && (
                      <span className="ml-2 rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] tracking-wider text-primary uppercase">
                        Subscribed
                      </span>
                    )}
                  </h3>
                  <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
                    <span className="font-medium text-muted-foreground">
                      Geohash:
                    </span>
                    <span className="text-right font-mono">
                      {data.id.replace("regional-", "").replace("sub-", "")}
                    </span>

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
          )
        })}

        {selectedLocation && (
          <Marker position={[selectedLocation.lat, selectedLocation.lng]}>
            <Popup>Your selected location</Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  )
}
