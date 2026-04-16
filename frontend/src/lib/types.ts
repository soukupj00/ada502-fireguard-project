/**
 * Core TypeScript type definitions for the FireGuard frontend.
 *
 * Defines all data models used in API communication with the backend,
 * including zones, risk readings, subscriptions, and HATEOAS response structures.
 *
 * Types document:
 * - GeoJSON features for map visualization
 * - Fire risk categories and scores
 * - User subscriptions and alerts
 * - HATEOAS link structures for REST discoverability
 *
 * @module lib/types
 */

/**
 * HATEOAS hyperlink for REST discoverability.
 *
 * Follows REST HAL specification for self-describing hypermedia.
 *
 * @interface HATEOASLink
 * @property {string} href - URI target of the link
 * @property {string} rel - Relationship type (self, create, update, delete, etc.)
 * @property {string} type - MIME type of the linked resource
 */
export interface HATEOASLink {
  href: string
  rel: string
  type: string
}

/**
 * Base for API responses containing optional HATEOAS links.
 *
 * Provides REST discoverability through hypermedia links and JSON-LD context.
 *
 * @interface BaseHATEOASResponse
 * @property {Record<string, string>} context - JSON-LD namespace context exposed as the "@context" field (optional)
 * @property {HATEOASLink[]} _links - Navigation and action links (optional)
 */
export interface BaseHATEOASResponse {
  "@context"?: Record<string, string>
  _links?: HATEOASLink[]
}

/**
 * Represents a monitored fire risk zone.
 *
 * A zone is a geographical area (identified by geohash) that is monitored
 * for fire risk. Zones can be regional (large) or local (small areas).
 *
 * @interface MonitoredZone
 * @property {string} geohash - Geohash identifier for the zone
 * @property {number} center_lat - Center latitude of zone
 * @property {number} center_lon - Center longitude of zone
 * @property {boolean} is_regional - True if zone is regional scale
 * @property {string | null} name - Display name or null
 * @property {string | null} last_updated - ISO 8601 timestamp of last update or null
 */
export interface MonitoredZone {
  geohash: string
  center_lat: number
  center_lon: number
  is_regional: boolean
  name: string | null
  last_updated: string | null
}

/**
 * Fire risk category severity level definition.
 *
 * @interface RiskLevel
 * @property {string} category - Risk category name (low, moderate, high, extreme)
 * @property {string} score_range - Human-readable score range (e.g., "0-20")
 * @property {string} description - Severity description and action guidance
 */
export interface RiskLevel {
  category: string
  score_range: string
  description: string
}

/**
 * Legend documenting all fire risk categories and thresholds.
 *
 * @interface RiskLegend
 * @property {string} title - Legend title
 * @property {string} description - Legend description
 * @property {RiskLevel[]} levels - Array of risk level definitions
 */
export interface RiskLegend {
  title: string
  description: string
  levels: RiskLevel[]
}

/**
 * Current fire risk reading for a specific zone/location.
 *
 * Contains geospatial coordinates, risk measurements, and temporal metadata.
 *
 * @interface FireRiskReading
 * @extends BaseHATEOASResponse
 * @property {string} geohash - Zone geohash identifier
 * @property {number} latitude - Reading latitude
 * @property {number} longitude - Reading longitude
 * @property {number | null} risk_score - Numerical risk score (0-100) or null
 * @property {string | null} risk_category - Category name (low/moderate/high/extreme) or null
 * @property {number} ttf - Time to fire / prediction hours
 * @property {string} prediction_timestamp - ISO 8601 timestamp when prediction was made
 * @property {string} updated_at - ISO 8601 timestamp of last update
 * @property {RiskLegend | null} risk_legend - Risk category legend or null
 */
export interface FireRiskReading extends BaseHATEOASResponse {
  geohash: string
  latitude: number
  longitude: number
  risk_score: number | null
  risk_category: string | null
  ttf: number
  prediction_timestamp: string
  updated_at: string
  risk_legend?: RiskLegend | null
}

/**
 * GeoJSON Feature properties for a fire risk zone.
 *
 * @interface GeoJSONProperties
 * @property {string} geohash - Zone identifier
 * @property {string | null} name - Display name or null
 * @property {boolean} is_regional - Zone scale indicator
 * @property {number | null} risk_score - Current risk score or null
 * @property {string | null} risk_category - Current risk category or null
 * @property {string | null} last_updated - ISO 8601 update timestamp or null
 */
export interface GeoJSONProperties {
  geohash: string
  name: string | null
  is_regional: boolean
  risk_score: number | null
  risk_category: string | null
  last_updated: string | null
}

/**
 * GeoJSON Point Feature with fire risk properties.
 *
 * Represents a single zone as a GeoJSON feature for map visualization.
 *
 * @interface GeoJSONFeature
 * @property {"Feature"} type - GeoJSON type indicator
 * @property {Object} geometry - Point geometry
 * @property {number[]} geometry.coordinates - [longitude, latitude] array
 * @property {GeoJSONProperties} properties - Zone and risk properties
 * @property {Record<string, string> | null} context - JSON-LD context exposed as the "@context" field or null
 * @property {HATEOASLink[] | null} _links - Navigation links or null
 */
export interface GeoJSONFeature {
  type: "Feature"
  geometry: {
    type: "Point"
    coordinates: [number, number] // [longitude, latitude]
  }
  properties: GeoJSONProperties
  "@context"?: Record<string, string> | null
  _links?: HATEOASLink[] | null
}

/**
 * GeoJSON FeatureCollection of fire risk zones.
 *
 * Represents all monitored zones as a single GeoJSON collection for maps.
 *
 * @interface GeoJSONFeatureCollection
 * @extends BaseHATEOASResponse
 * @property {"FeatureCollection"} type - GeoJSON collection type
 * @property {GeoJSONFeature[]} features - Array of zone features
 * @property {RiskLegend | null} risk_legend - Legend for risk categories or null
 */
export interface GeoJSONFeatureCollection extends BaseHATEOASResponse {
  type: "FeatureCollection"
  features: GeoJSONFeature[]
  risk_legend?: RiskLegend | null
}

/**
 * Backward-compatible alias for GeoJSON response.
 * @type {GeoJSONFeatureCollection}
 */
export type GeoJSONResponse = GeoJSONFeatureCollection

/**
 * User subscription to fire alerts for a zone.
 *
 * @interface SubscriptionResponse
 * @extends BaseHATEOASResponse
 * @property {string} geohash - Subscribed zone geohash
 * @property {"active" | "pending"} status - Subscription activation status
 * @property {string} message - Status message
 * @property {number | null} current_risk - Current risk score in zone or null
 */
export interface SubscriptionResponse extends BaseHATEOASResponse {
  geohash: string
  status: "active" | "pending"
  message: string
  current_risk: number | null
}

/**
 * Request payload for creating a zone subscription.
 *
 * Can be a simple geohash string or an object with additional parameters.
 *
 * @type {string | {geohash: string}}
 */
export type SubscriptionRequest =
  | string
  | {
      geohash: string
    }

/**
 * API error response structure.
 *
 * @interface ApiError
 * @property {string} message - Error message
 * @property {Object} response - API response object
 * @property {Object} response.data - Response body
 * @property {string} response.data.detail - Detail message from backend
 */
export interface ApiError {
  message?: string
  response?: {
    data?: {
      detail?: string
    }
  }
}

/**
 * User's list of active zone subscriptions.
 *
 * @interface UserSubscriptionListResponse
 * @extends BaseHATEOASResponse
 * @property {string[]} geohashes - Array of subscribed zone geohashes
 */
export interface UserSubscriptionListResponse extends BaseHATEOASResponse {
  geohashes: string[]
}

/**
 * Real-time fire risk data from SSE stream.
 *
 * Streamed from backend for specific zone during SSE connection.
 *
 * @interface StreamRiskData
 * @property {string} location_id - Zone identifier
 * @property {string} risk_category - Risk category (low/moderate/high/extreme)
 * @property {number} risk_score - Numerical risk score
 * @property {number} ttf - Time to fire in hours
 * @property {string} timestamp - ISO 8601 timestamp
 */
export interface StreamRiskData {
  location_id: string
  risk_category: string
  risk_score: number
  ttf: number
  timestamp: string
}

/**
 * Geospatial search result coordinates.
 *
 * @interface GeoSearchResult
 * @property {Object} location - Coordinate pair
 * @property {number} location.x - Longitude
 * @property {number} location.y - Latitude
 */
export interface GeoSearchResult {
  location: {
    x: number
    y: number
  }
}
