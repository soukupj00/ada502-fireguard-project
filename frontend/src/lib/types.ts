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
    coordinates: [number, number]
  }
  properties: GeoJSONProperties
}

export interface GeoJSONResponse {
  type: "FeatureCollection"
  features: GeoJSONFeature[]
}

export interface FireRiskReading {
  geohash: string
  latitude: number
  longitude: number
  risk_score: number | null
  risk_category: string | null
  ttf: number
  prediction_timestamp: string
  updated_at: string
}

export interface SubscriptionRequest {
  latitude?: number | null
  longitude?: number | null
  geohash?: string | null
}

export interface SubscriptionResponse {
  geohash: string
  status: string
  message: string
  current_risk: number | null
}

export interface ApiError {
  response?: {
    data?: {
      detail?: string
    }
  }
  message: string
}

export interface GeoSearchResult {
  location: {
    x: number // longitude
    y: number // latitude
    label: string // formatted address
    bounds: [
      [number, number], // southWest
      [number, number], // northEast
    ]
    raw: unknown // Raw response from provider
  }
}
