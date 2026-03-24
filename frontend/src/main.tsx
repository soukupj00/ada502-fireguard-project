import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import "./index.css"
import App from "./App.tsx"
import keycloak from "./keycloak"
import { ThemeProvider } from "@/components/theme-provider.tsx"
import { Toaster } from "@/components/ui/sonner"

keycloak
  .init({
    onLoad: "check-sso", // CHANGE THIS: Check silently, don't force login
    silentCheckSsoRedirectUri:
      window.location.origin + "/silent-check-sso.html", // Required for check-sso to work smoothly
  })
  .then((authenticated: boolean) => {
    const rootElement = document.getElementById("root")
    if (!rootElement) throw new Error("Root element not found")

    createRoot(rootElement).render(
      <StrictMode>
        <ThemeProvider>
          {/* You can pass the auth state if you want, but keycloak object is global */}
          <App isAuthenticated={authenticated} />
          <Toaster />
        </ThemeProvider>
      </StrictMode>
    )
  })
  .catch((error: unknown) => {
    console.error("Keycloak initialization failed", error)
  })
