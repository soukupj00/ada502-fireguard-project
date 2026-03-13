export interface GeoJSONFeature {
  type: "Feature"
  geometry: {
    type: "Point"
    coordinates: [number, number]
  }
  properties: {
    geohash: string
    name: string
    is_regional: boolean
    risk_score: number | null
    risk_category: string | null
    last_updated: string
  }
}

export interface GeoJSONResponse {
  type: "FeatureCollection"
  features: GeoJSONFeature[]
}
