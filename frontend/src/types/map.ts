import type { LatLngBoundsExpression } from "leaflet"
import type { GeoJSONFeature } from "@/lib/types"

/**
 * Represents a processed map feature ready to be rendered on the Leaflet map.
 * This is derived from the raw GeoJSON feature returned by the API.
 */
export interface MapFeature {
  /** The unique identifier for the feature (typically the geohash) */
  id: string

  /** The display name of the zone (e.g., "Regional Zone u47") */
  name: string

  /** The geographical bounds of the rectangle [SouthWest, NorthEast] */
  bounds: LatLngBoundsExpression

  /** The calculated fire risk probability (0-100) */
  riskScore: number

  /** The textual category of the risk (e.g., "High", "Low") */
  riskCategory: string

  /** Whether this is a user-subscribed zone */
  isRegional: boolean
}

/**
 * Represents a feature that was skipped during processing
 * because it was invalid or irrelevant (e.g., sea).
 */
export interface SkippedFeature {
  index: number
  reason: string
  feature: GeoJSONFeature["properties"]
}
