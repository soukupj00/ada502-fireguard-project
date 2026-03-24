import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import "./index.css"
import App from "./App.tsx"
import keycloak from "./keycloak"

keycloak
  .init({
    onLoad: "login-required",
  })
  .then((authenticated: boolean) => {
    if (!authenticated) {
      window.location.reload()
      return
    }

    const rootElement = document.getElementById("root")

    if (!rootElement) {
      throw new Error("Root element not found")
    }

    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>
    )
  })
  .catch((error: unknown) => {
    console.error("Keycloak initialization failed", error)
  })