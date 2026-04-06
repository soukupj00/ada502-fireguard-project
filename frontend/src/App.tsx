import { ThemeProvider } from "@/components/theme-provider"
import { Navbar } from "@/components/Navbar"
import HomePage from "@/pages/HomePage"
import DashboardPage from "@/pages/DashboardPage"
import {
  BrowserRouter as Router,
  Navigate,
  Route,
  Routes,
} from "react-router-dom"
import type { JSX } from "react"

import { projectConfig } from "@/config"

// Protected Route Wrapper declared outside of App
const ProtectedRoute = ({
  children,
  isAuthenticated,
}: {
  children: JSX.Element
  isAuthenticated: boolean
}) => {
  if (!isAuthenticated) {
    return <Navigate to="/" replace />
  }
  return children
}

// Redirect logged-in users away from the public home page
const PublicRoute = ({
  children,
  isAuthenticated,
}: {
  children: JSX.Element
  isAuthenticated: boolean
}) => {
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  return children
}

function App({ isAuthenticated }: { isAuthenticated: boolean }) {
  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <Router>
        <div className="flex min-h-screen flex-col bg-background font-sans text-foreground">
          <Navbar isAuthenticated={isAuthenticated} />

          <Routes>
            <Route
              path="/"
              element={
                <PublicRoute isAuthenticated={isAuthenticated}>
                  <HomePage isAuthenticated={isAuthenticated} />
                </PublicRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            {/* Catch-all redirect */}
            <Route
              path="*"
              element={
                <Navigate to={isAuthenticated ? "/dashboard" : "/"} replace />
              }
            />
          </Routes>

          <footer className="mt-auto border-t bg-muted/5 py-8 text-sm text-muted-foreground">
            <div className="container mx-auto px-4">
              <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
                <div className="text-left">
                  <p className="font-semibold text-foreground">
                    FireGuard Project
                  </p>
                  <p>
                    Developed for {projectConfig.university.course} at{" "}
                    {projectConfig.university.name},{" "}
                    {projectConfig.university.city}.
                  </p>
                  <p className="mt-1 text-xs italic">
                    This project is for educational purposes; all rights are
                    waived where applicable.
                  </p>
                </div>
                <div className="flex flex-col items-end text-right">
                  <p>Authors: {projectConfig.authors.join(", ")}</p>
                  <p>Released under {projectConfig.license}</p>
                  <p className="mt-1 opacity-70">
                    &copy; {new Date().getFullYear()} FireGuard. All rights
                    reserved.
                  </p>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </Router>
    </ThemeProvider>
  )
}

export default App
