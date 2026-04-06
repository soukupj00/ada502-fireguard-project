import { MapView } from "@/components/map/map-view"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import keycloak from "@/keycloak"
import { LogIn, User, UserPlus } from "lucide-react"
import { useZones } from "@/hooks/use-zones"
import { useMemo } from "react"
import Geohash from "latlon-geohash"
import type { MapFeature } from "@/types/map"
import { AnalyticsWidget } from "@/components/AnalyticsWidget"
import { HistoryWidget } from "@/components/HistoryWidget"
import { RiskLegendWidget } from "@/components/RiskLegendWidget"

export default function HomePage({
  isAuthenticated,
}: {
  isAuthenticated: boolean
}) {
  const handleLogin = () => keycloak.login()
  const handleRegister = () => keycloak.register()

  // For the public home page, ONLY fetch the regional zones!
  const { zones, isLoading, isError } = useZones(true)

  const mapFeatures = useMemo(() => {
    if (!zones) return []

    return zones.features
      .map((feature): MapFeature | null => {
        const { geohash, risk_score, name, risk_category } = feature.properties

        if (!geohash || risk_score === null) return null

        try {
          const bounds = Geohash.bounds(geohash)

          return {
            id: `regional-${geohash}`,
            name: name || `Regional Zone ${geohash}`,
            bounds: [
              [bounds.sw.lat, bounds.sw.lon],
              [bounds.ne.lat, bounds.ne.lon],
            ],
            riskScore: risk_score,
            riskCategory: risk_category ?? "N/A",
            isRegional: true,
          }
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (e) {
          return null
        }
      })
      .filter((item): item is MapFeature => item !== null)
  }, [zones])

  return (
    <div className="container mx-auto flex-1 p-4 py-8">
      {/* PUBLIC MAP: Everyone sees this */}
      <Card className="overflow-hidden border-muted/40 shadow-lg">
        <CardHeader className="border-b bg-muted/10 pb-6">
          <CardTitle className="text-2xl">Fire Probability Map</CardTitle>
          <CardDescription className="text-base text-muted-foreground">
            Visualize fire risk across different regions based on real-time
            environmental data analysis.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <div className="relative z-0 h-150 w-full overflow-hidden rounded-md border shadow-inner">
            <MapView
              features={mapFeatures}
              isLoading={isLoading}
              isError={isError}
            />
          </div>
          <div className="mt-6">
            <RiskLegendWidget legend={zones?.risk_legend} />
          </div>
        </CardContent>
      </Card>

      <div className="mt-8">
        <AnalyticsWidget />
      </div>

      <HistoryWidget />

      {!isAuthenticated && (
        <Card className="mt-8 border-dashed bg-muted/30">
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <User className="h-6 w-6" />
            </div>
            <h3 className="mb-2 text-lg font-semibold">
              Track Specific Regions
            </h3>
            <p className="mb-6 max-w-md text-muted-foreground">
              Create an account or log in to subscribe to specific locations,
              save your preferences, and receive real-time alerts.
            </p>
            <div className="flex items-center gap-4">
              <Button onClick={handleLogin} variant="outline" className="gap-2">
                <LogIn className="h-4 w-4" />
                Sign In
              </Button>
              <Button onClick={handleRegister} className="gap-2">
                <UserPlus className="h-4 w-4" />
                Register to Subscribe
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
