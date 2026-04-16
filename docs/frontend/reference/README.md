# FireGuard Frontend API

FireGuard Frontend Public API and Type Exports.

This module serves as the entry point for TypeDoc API documentation generation.
Exports all public-facing types and custom hooks that should be documented.

Public exports include:
- Custom React hooks for fire risk monitoring and subscriptions
- TypeScript type definitions for API responses and domain entities
- Integration utilities for backend API and realt-time services

## Interfaces

- [ApiError](interfaces/ApiError.md)
- [BaseHATEOASResponse](interfaces/BaseHATEOASResponse.md)
- [FireRiskReading](interfaces/FireRiskReading.md)
- [GeoJSONFeature](interfaces/GeoJSONFeature.md)
- [GeoJSONFeatureCollection](interfaces/GeoJSONFeatureCollection.md)
- [GeoJSONProperties](interfaces/GeoJSONProperties.md)
- [GeoSearchResult](interfaces/GeoSearchResult.md)
- [HATEOASLink](interfaces/HATEOASLink.md)
- [MonitoredZone](interfaces/MonitoredZone.md)
- [RiskLegend](interfaces/RiskLegend.md)
- [RiskLevel](interfaces/RiskLevel.md)
- [StreamRiskData](interfaces/StreamRiskData.md)
- [SubscriptionResponse](interfaces/SubscriptionResponse.md)
- [UserSubscriptionListResponse](interfaces/UserSubscriptionListResponse.md)

## Type Aliases

- [GeoJSONResponse](type-aliases/GeoJSONResponse.md)
- [SubscriptionRequest](type-aliases/SubscriptionRequest.md)

## Functions

- [useLocationStream](functions/useLocationStream.md)
- [useMqttAlerts](functions/useMqttAlerts.md)
- [useSubscriptions](functions/useSubscriptions.md)
- [useThingspeakData](functions/useThingspeakData.md)
- [useZones](functions/useZones.md)
