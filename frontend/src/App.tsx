import { MapView } from "@/components/map/map-view"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import { Button } from "@/components/ui/button"

import { ThemeProvider } from "@/components/theme-provider"
import { ModeToggle } from "@/components/mode-toggle"
import TestRiskAPI from "@/components/TestRiskAPI";


function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <div className="flex min-h-screen flex-col bg-background font-sans text-foreground">
        <header className="border-b bg-card">
          <div className="container mx-auto flex items-center justify-between px-4 py-4">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-xs font-bold text-primary-foreground shadow-sm">
                FG
              </div>
              <h1 className="text-xl font-bold tracking-tight">FireGuard</h1>
            </div>
            <ModeToggle />
          </div>
        </header>
        <main className="container mx-auto flex-1 p-4 py-8">
          <Card>
            <CardHeader>
              <CardTitle>Location</CardTitle>
              <CardDescription>Here you can see the fire risk for your location</CardDescription>
            </CardHeader>
            <CardContent>
              <TestRiskAPI geohash="u67" />
              <Button variant="outline">Change location</Button>
            </CardContent>
          </Card>



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
        </main>
        <footer className="border-t bg-muted/5 py-6 text-center text-sm text-muted-foreground">
          <div className="container mx-auto">
            &copy; {new Date().getFullYear()} FireGuard Project. All rights
            reserved.
          </div>
        </footer>
      </div>
    </ThemeProvider>
  )
}

export default App
