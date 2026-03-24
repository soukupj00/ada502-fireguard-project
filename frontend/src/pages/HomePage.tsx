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

export default function HomePage({
  isAuthenticated,
}: {
  isAuthenticated: boolean
}) {
  const handleLogin = () => keycloak.login()
  const handleRegister = () => keycloak.register()

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
          <div className="relative z-0 h-[600px] w-full overflow-hidden rounded-md border shadow-inner">
            <MapView />
          </div>
          <div className="mt-6 grid grid-cols-2 justify-center gap-4 rounded-lg border bg-muted/20 p-4 text-sm md:grid-cols-4">
            <div className="flex items-center justify-center gap-2">
              <div className="h-4 w-4 rounded bg-red-500 shadow-sm ring-1 ring-red-600/20"></div>
              <span className="font-medium text-red-700 dark:text-red-400">
                High Risk (&gt; 80%)
              </span>
            </div>
            <div className="flex items-center justify-center gap-2">
              <div className="h-4 w-4 rounded bg-orange-500 shadow-sm ring-1 ring-orange-600/20"></div>
              <span className="font-medium text-orange-700 dark:text-orange-400">
                Medium-High (&gt; 50%)
              </span>
            </div>
            <div className="flex items-center justify-center gap-2">
              <div className="h-4 w-4 rounded bg-yellow-500 shadow-sm ring-1 ring-yellow-600/20"></div>
              <span className="font-medium text-yellow-700 dark:text-yellow-400">
                Medium-Low (&gt; 20%)
              </span>
            </div>
            <div className="flex items-center justify-center gap-2">
              <div className="h-4 w-4 rounded bg-green-500 shadow-sm ring-1 ring-green-600/20"></div>
              <span className="font-medium text-green-700 dark:text-green-400">
                Low Risk (&lt; 20%)
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

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
