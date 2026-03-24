import { Button } from "@/components/ui/button"
import { ModeToggle } from "@/components/mode-toggle"
import { LogIn, LogOut, User, UserPlus } from "lucide-react"
import { Link } from "react-router-dom"
import keycloak from "@/keycloak"

interface NavbarProps {
  isAuthenticated: boolean
}

export function Navbar({ isAuthenticated }: NavbarProps) {
  const handleLogin = () => keycloak.login()
  const handleRegister = () => keycloak.register()
  const handleLogout = () => keycloak.logout()

  return (
    <header className="border-b bg-card">
      <div className="container mx-auto flex items-center justify-between px-4 py-4">
        {/* If logged in, logo links to dashboard. If not, to home */}
        <Link
          to={isAuthenticated ? "/dashboard" : "/"}
          className="flex items-center gap-2"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-xs font-bold text-primary-foreground shadow-sm">
            FG
          </div>
          <h1 className="text-xl font-bold tracking-tight">FireGuard</h1>
        </Link>
        <div className="flex items-center gap-4">
          <ModeToggle />

          {isAuthenticated ? (
            <div className="ml-2 flex items-center gap-4 border-l border-border/50 pl-4">
              <div className="flex items-center gap-2 rounded-full border border-border/50 bg-muted/40 px-3 py-1.5 text-sm text-muted-foreground">
                <User className="h-4 w-4" />
                <span>
                  {keycloak.tokenParsed?.preferred_username || "User"}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="gap-2"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </Button>
            </div>
          ) : (
            <div className="ml-2 flex items-center gap-2 border-l border-border/50 pl-4">
              <Button
                variant="ghost"
                onClick={handleLogin}
                size="sm"
                className="gap-2"
              >
                <LogIn className="h-4 w-4" />
                Sign In
              </Button>
              <Button onClick={handleRegister} size="sm" className="gap-2">
                <UserPlus className="h-4 w-4" />
                Register
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
