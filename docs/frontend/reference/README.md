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
- [MapFeature](interfaces/MapFeature.md)
- [MonitoredZone](interfaces/MonitoredZone.md)
- [RiskLegend](interfaces/RiskLegend.md)
- [RiskLevel](interfaces/RiskLevel.md)
- [SkippedFeature](interfaces/SkippedFeature.md)
- [StreamRiskData](interfaces/StreamRiskData.md)
- [SubscriptionResponse](interfaces/SubscriptionResponse.md)
- [ThingSpeakChannel](interfaces/ThingSpeakChannel.md)
- [ThingSpeakFeed](interfaces/ThingSpeakFeed.md)
- [ThingSpeakResponse](interfaces/ThingSpeakResponse.md)
- [UserSubscriptionListResponse](interfaces/UserSubscriptionListResponse.md)

## Type Aliases

- [GeoJSONResponse](type-aliases/GeoJSONResponse.md)
- [SubscriptionRequest](type-aliases/SubscriptionRequest.md)

## Variables

- [API\_URL](variables/API_URL.md)
- [KEYCLOAK\_CLIENT\_ID](variables/KEYCLOAK_CLIENT_ID.md)
- [KEYCLOAK\_REALM](variables/KEYCLOAK_REALM.md)
- [KEYCLOAK\_URL](variables/KEYCLOAK_URL.md)
- [MQTT\_BROKER\_URL](variables/MQTT_BROKER_URL.md)
- [MQTT\_PASSWORD](variables/MQTT_PASSWORD.md)
- [MQTT\_USERNAME](variables/MQTT_USERNAME.md)
- [projectConfig](variables/projectConfig.md)
- [THINGSPEAK\_CHANNEL\_ID](variables/THINGSPEAK_CHANNEL_ID.md)
- [THINGSPEAK\_READ\_API\_KEY](variables/THINGSPEAK_READ_API_KEY.md)

## Functions

- [buildApiUrl](functions/buildApiUrl.md)
- [cn](functions/cn.md)
- [deleteSubscription](functions/deleteSubscription.md)
- [fetchHistory](functions/fetchHistory.md)
- [fetchJson](functions/fetchJson.md)
- [fetchSecureData](functions/fetchSecureData.md)
- [fetchWithAuth](functions/fetchWithAuth.md)
- [fetchZones](functions/fetchZones.md)
- [subscribeToLocation](functions/subscribeToLocation.md)
- [useLocationStream](functions/useLocationStream.md)
- [useMqttAlerts](functions/useMqttAlerts.md)
- [useSubscriptions](functions/useSubscriptions.md)
- [useThingspeakData](functions/useThingspeakData.md)
- [useZones](functions/useZones.md)
