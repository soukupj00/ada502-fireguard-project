// frontend/src/keycloak.ts
import Keycloak from "keycloak-js"

const keycloakConfig = {
  // relative path for Nginx/Vite
  url: import.meta.env.VITE_KEYCLOAK_URL || "/auth",
  realm: "FireGuard",
  clientId: "frontend-client", // Updated from 'react-app'
}

const keycloak = new Keycloak(keycloakConfig)

export default keycloak
