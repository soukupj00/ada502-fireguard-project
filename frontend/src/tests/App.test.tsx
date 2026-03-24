import { render, screen } from "@testing-library/react"
import App from "../App.tsx"

describe("App", () => {
  it("renders the main heading", () => {
    render(<App isAuthenticated={false} />)

    // Adjust this text to match whatever is currently in your App.tsx
    // For example, if your App.tsx says "FireGuard", search for that.
    const heading = screen.getByRole("heading", { level: 1 })
    expect(heading).toBeInTheDocument()
  })
})
