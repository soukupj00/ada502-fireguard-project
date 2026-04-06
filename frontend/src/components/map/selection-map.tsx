import { useEffect, useMemo } from "react"
import {
  MapContainer,
  TileLayer,
  Marker,
  useMap,
  useMapEvents,
  Rectangle,
} from "react-leaflet"
import "leaflet/dist/leaflet.css"
import "leaflet-geosearch/dist/geosearch.css"
import type { LatLngBoundsExpression, LatLngExpression } from "leaflet"
import L from "leaflet"
import { GeoSearchControl, OpenStreetMapProvider } from "leaflet-geosearch"
import type { GeoSearchResult } from "@/lib/types"
import type { MapFeature } from "@/types/map"
import { useZones } from "@/hooks/use-zones"
import Geohash from "latlon-geohash"
import { getRiskStyle } from "./map-styles"
import { MapResizer } from "./map-resizer"

// Fix for the default marker icon in react-leaflet
delete (L.Icon.Default.prototype as unknown as { _getIconUrl: unknown })
  ._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
})

interface SelectionMapProps {
  center?: LatLngExpression
  zoom?: number
  selectedLocation: { lat: number; lng: number } | null
  onLocationSelect: (lat: number, lng: number) => void
}

function SearchField({
  onLocationSelect,
}: {
  onLocationSelect: (lat: number, lng: number) => void
}) {
  const map = useMap()

  useEffect(() => {
    const provider = new OpenStreetMapProvider()

    // @ts-expect-error - geosearch events aren't natively typed in leaflet's event map
    const searchControl = new GeoSearchControl({
      provider: provider,
      style: "bar",
      showMarker: false, // We will handle our own marker
      showPopup: false,
      autoClose: true,
      retainZoomLevel: false,
      animateZoom: true,
      keepResult: true,
      searchLabel: "Enter address, city, or coordinates",
    })

    map.addControl(searchControl)

    // Listen for the location found event from geosearch
    const handleLocationFound: L.LeafletEventHandlerFn = (event) => {
      const e = event as L.LeafletEvent & GeoSearchResult
      onLocationSelect(e.location.y, e.location.x)
    }

    map.on("geosearch/showlocation", handleLocationFound)

    return () => {
      map.removeControl(searchControl)
      map.off("geosearch/showlocation", handleLocationFound)
    }
  }, [map, onLocationSelect])

  return null
}

function LocationMarker({
  selectedLocation,
  onLocationSelect,
}: {
  selectedLocation: { lat: number; lng: number } | null
  onLocationSelect: (lat: number, lng: number) => void
}) {
  useMapEvents({
    click(e) {
      onLocationSelect(e.latlng.lat, e.latlng.lng)
    },
  })

  return selectedLocation === null ? null : (
    <Marker position={[selectedLocation.lat, selectedLocation.lng]} />
  )
}

export function SelectionMap({
  center = [58.359375, 10.546875] as LatLngExpression,
  zoom = 6,
  selectedLocation,
  onLocationSelect,
}: SelectionMapProps) {
  // Load zones to draw the invisible grid for clicking reference
  const { zones } = useZones(false)

  const mapData = useMemo(() => {
    if (!zones) return []

    return zones.features
      .map((feature): MapFeature | null => {
        const { geohash, risk_score, name, risk_category, is_regional } =
          feature.properties

        if (!geohash || risk_score === null) return null

        try {
          const bounds = Geohash.bounds(geohash)
          const leafletBounds: LatLngBoundsExpression = [
            [bounds.sw.lat, bounds.sw.lon],
            [bounds.ne.lat, bounds.ne.lon],
          ]

          return {
            id: geohash,
            name: name || "",
            bounds: leafletBounds,
            riskScore: risk_score,
            riskCategory: risk_category ?? "N/A",
            isRegional: is_regional,
          }
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_e) {
          return null
        }
      })
      .filter((item): item is MapFeature => item !== null)
  }, [zones])

  return (
    <div className="relative z-0 h-full w-full">
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        style={{
          height: "100%",
          width: "100%",
          minHeight: "400px",
          cursor: "crosshair",
        }}
      >
        <MapResizer />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Draw the transparent grid for visual reference so users know where the zones are */}
        {mapData.map((data) => {
          const style = getRiskStyle(data.riskScore, data.isRegional)
          return (
            <Rectangle
              key={`grid-${data.id}`}
              bounds={data.bounds}
              interactive={false} // Make it unclickable so the map click registers!
              pathOptions={{
                color: style.color,
                fillColor: "transparent", // Only show the border
                fillOpacity: 0,
                weight: 1,
                stroke: true,
                dashArray: data.isRegional ? undefined : "5, 5",
              }}
            />
          )
        })}

        <SearchField onLocationSelect={onLocationSelect} />

        <LocationMarker
          selectedLocation={selectedLocation}
          onLocationSelect={onLocationSelect}
        />
      </MapContainer>
    </div>
  )
}
