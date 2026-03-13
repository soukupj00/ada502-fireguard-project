import { useEffect, useState } from "react"

function TestRiskAPI() {
  //Funktion asks for current fire risk using geohash
  const [risk, setRisk] = useState<number | null>(null)
  const geohash = "u67"

  useEffect(() => {
    async function fetchRisk() {
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/risk/${geohash}`
        )
        if (!response.ok) throw new Error("API request failed")
        const data = await response.json()
        setRisk(data.risk_score)
      } catch (err) {
        console.error(err)
      }
    }
    fetchRisk()
  }, [])

  return <div>{risk !== null ? `Fire Risk Level: ${risk}` : "Loading..."}</div>
}

export default TestRiskAPI
