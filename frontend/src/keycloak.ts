/**
 * Keycloak authentication client initialization and configuration.
 *
 * Configures and exports a Keycloak instance for OpenID Connect (OIDC) authentication.
 * Shared across the application for SSO, user authentication, and token management.
 *
 * @module keycloak
 */

import Keycloak from "keycloak-js"

/**
 * Keycloak client configuration.
 *
 * Uses environment variables with defaults for development.
 * In production, Nginx reverse proxy routes calls to Keycloak container.
 *
 * @type {Object}
 * @property {string} url - Keycloak server URL (defaults to /auth for proxied access)
 * @property {string} realm - Keycloak realm name for FireGuard
 * @property {string} clientId - OAuth2 client ID registered in Keycloak
 */
const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || "/auth",
  realm: "FireGuard",
  clientId: "frontend-client",
}

/**
 * Initialized Keycloak instance for authentication.
 *
 * Used throughout the app to manage user authentication via OIDC.
 * Access user tokens and authentication status via properties:
 * - keycloak.authenticated: boolean
 * - keycloak.token: JWT string
 * - keycloak.updateToken(minValidity): Promise<boolean>
 *
 * @type {Object}
 */
const keycloak = new Keycloak(keycloakConfig)

export default keycloak
