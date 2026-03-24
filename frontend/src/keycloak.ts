import Keycloak from "keycloak-js"

const keycloakConfig = {
  url: "http://localhost:8080", // The Keycloak URL
  realm: "FireGuard", // The realm you created
  clientId: "react-app", // The client ID you created
}

const keycloak = new Keycloak(keycloakConfig)

export default keycloak
