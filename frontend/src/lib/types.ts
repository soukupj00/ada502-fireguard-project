export interface HATEOASLink {
  href: string
  rel: string
  type: string
}

export interface BaseHATEOASResponse {
  "@context"?: Record<string, string>
  _links?: HATEOASLink[]
}

export interface MonitoredZone {
  geohash: string
  center_lat: number
  center_lon: number
  is_regional: boolean
  name: string | null
  last_updated: string | null
}

export interface RiskLevel {
  category: string
  score_range: string
  description: string
}

export interface RiskLegend {
  title: string
  description: string
  levels: RiskLevel[]
}

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

export interface GeoJSONProperties {
  geohash: string
  name: string | null
  is_regional: boolean
  risk_score: number | null
  risk_category: string | null
  last_updated: string | null
}

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

export interface GeoJSONFeatureCollection extends BaseHATEOASResponse {
  type: "FeatureCollection"
  features: GeoJSONFeature[]
  risk_legend?: RiskLegend | null
}

// Backward-compatible alias still used by hooks/widgets.
export type GeoJSONResponse = GeoJSONFeatureCollection

export interface SubscriptionResponse extends BaseHATEOASResponse {
  geohash: string
  status: "active" | "pending"
  message: string
  current_risk: number | null
}

export type SubscriptionRequest =
  | string
  | {
      geohash: string
    }

export interface ApiError {
  message?: string
  response?: {
    data?: {
      detail?: string
    }
  }
}

export interface UserSubscriptionListResponse extends BaseHATEOASResponse {
  geohashes: string[]
}

export interface StreamRiskData {
  location_id: string
  risk_category: string // Changed from risk_level to risk_category
  risk_score: number
  ttf: number
  timestamp: string
}

export interface GeoSearchResult {
  location: {
    x: number
    y: number
  }
}
