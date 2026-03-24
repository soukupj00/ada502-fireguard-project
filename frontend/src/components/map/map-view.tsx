import {
  MapContainer,
  Popup,
  Rectangle,
  TileLayer,
  useMap,
} from "react-leaflet"
import "leaflet/dist/leaflet.css"
import type { LatLngBoundsExpression, LatLngExpression } from "leaflet"
import L from "leaflet"
import { useZones } from "@/hooks/use-zones"
import { useEffect, useMemo } from "react"
import Geohash from "latlon-geohash"
import type { MapFeature } from "@/types/map"

interface MapViewProps {
  center?: LatLngExpression
  zoom?: number
}

function AutoZoom({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap()
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 })
    }
  }, [bounds, map])
  return null
}

export function MapView({
  center = [58.359375, 10.546875] as LatLngExpression,
  zoom = 6,
}: MapViewProps) {
  const { zones, isLoading, isError } = useZones(false)

  const getColor = (riskScore: number) => {
    if (riskScore >= 80) return "#ef4444" // red-500
    if (riskScore >= 50) return "#f97316" // orange-500
    if (riskScore >= 20) return "#eab308" // yellow-500
    return "#22c55e" // green-500
  }

  const mapData = useMemo(() => {
    if (!zones) return []

    const features = zones.features
      .map((feature): MapFeature | null => {
        const { geohash, risk_score, name, risk_category, is_regional } =
          feature.properties

        if (!geohash || risk_score === null) {
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
            name:
              name ||
              (is_regional
                ? `Regional Zone ${geohash}`
                : `Personal Zone ${geohash}`),
            bounds: leafletBounds,
            riskScore: risk_score,
            riskCategory: risk_category ?? "N/A",
            isRegional: is_regional,
          }
        } catch (e) {
          console.error(`Invalid geohash: ${geohash}`, e)
          return null
        }
      })
      .filter((item): item is MapFeature => item !== null)

    // Sort: regional first, then user zones (so user zones are rendered on top)
    return [...features].sort((a, b) => {
      if (a.isRegional === b.isRegional) return 0
      return a.isRegional ? -1 : 1
    })
  }, [zones])

  const userZonesBounds = useMemo(() => {
    const userZones = mapData.filter((f) => !f.isRegional)
    if (userZones.length === 0) return null

    const bounds = L.latLngBounds([])
    userZones.forEach((zone) => {
      bounds.extend(zone.bounds)
    })
    return bounds.isValid()
      ? (bounds as unknown as LatLngBoundsExpression)
      : null
  }, [mapData])

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

        <AutoZoom bounds={userZonesBounds} />

        {mapData.map((data) => (
          <Rectangle
            key={data.id}
            bounds={data.bounds}
            pathOptions={{
              color: getColor(data.riskScore),
              fillColor: getColor(data.riskScore),
              fillOpacity: data.isRegional ? 0.4 : 0.7,
              weight: data.isRegional ? 1 : 3,
              stroke: !data.isRegional,
              dashArray: data.isRegional ? undefined : "5, 5",
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
