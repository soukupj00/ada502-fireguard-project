// Mock data for fire probability
// Each item represents a square area on the map

export const mockFireData = [
  {
    id: 1,
    bounds: [
      [51.505, -0.09],
      [51.515, -0.08],
    ],
    probability: 0.9, // High risk
  },
  {
    id: 2,
    bounds: [
      [51.515, -0.09],
      [51.525, -0.08],
    ],
    probability: 0.6, // Medium risk
  },
  {
    id: 3,
    bounds: [
      [51.505, -0.1],
      [51.515, -0.09],
    ],
    probability: 0.3, // Low risk
  },
  {
    id: 4,
    bounds: [
      [51.515, -0.1],
      [51.525, -0.09],
    ],
    probability: 0.1, // Very low risk
  },
]
