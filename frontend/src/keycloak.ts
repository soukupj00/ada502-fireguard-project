import Keycloak from "keycloak-js"

const keycloakConfig = {
  // Use a relative path. Nginx/Vite will route this to the Keycloak container.
  url: import.meta.env.VITE_KEYCLOAK_URL || "/auth",
  realm: "FireGuard",
  clientId: "react-app",
}

const keycloak = new Keycloak(keycloakConfig)

export default keycloak
