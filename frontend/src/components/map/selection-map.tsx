import { useEffect } from "react"
import {
  MapContainer,
  TileLayer,
  Marker,
  useMap,
  useMapEvents,
} from "react-leaflet"
import "leaflet/dist/leaflet.css"
import "leaflet-geosearch/dist/geosearch.css"
import type { LatLngExpression } from "leaflet"
import L from "leaflet"
import { GeoSearchControl, OpenStreetMapProvider } from "leaflet-geosearch"
import type { GeoSearchResult } from "@/lib/types"

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
    const handleLocationFound = (e: GeoSearchResult) => {
      onLocationSelect(e.location.y, e.location.x)
    }

    // @ts-expect-error - geosearch events aren't natively typed in leaflet's event map
    map.on("geosearch/showlocation", handleLocationFound)

    return () => {
      map.removeControl(searchControl)
      // @ts-expect-error - geosearch events aren't natively typed in leaflet's event map
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
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <SearchField onLocationSelect={onLocationSelect} />

        <LocationMarker
          selectedLocation={selectedLocation}
          onLocationSelect={onLocationSelect}
        />
      </MapContainer>
    </div>
  )
}
