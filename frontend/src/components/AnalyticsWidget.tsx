"use client"

import { useMemo } from "react"
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { useThingspeakData } from "@/hooks/use-thingspeak-data"

const chartConfig = {
  temperature: {
    label: "Temperature (°C)",
    color: "hsl(var(--chart-1))",
  },
  riskScore: {
    label: "Risk Score (0-100)",
    color: "hsl(var(--chart-2))",
  },
  humidity: {
    label: "Humidity (%)",
    color: "hsl(var(--chart-3))",
  },
} satisfies ChartConfig

export function AnalyticsWidget() {
  const { data, isLoading, isError } = useThingspeakData(24) // Fetch last 24 results

  const chartData = useMemo(() => {
    if (!data?.feeds) return []

    return data.feeds.map((feed) => {
      return {
        // Parse time nicely for the x-axis
        time: new Date(feed.created_at).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        // Map fields to what they represent (adjust based on your actual ThingSpeak setup)
        // Assume field1=temperature, field2=humidity, field3=riskScore
        temperature: parseFloat(feed.field1 || "0"),
        humidity: parseFloat(feed.field2 || "0"),
        riskScore: parseFloat(feed.field3 || "0"),
      }
    })
  }, [data])

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analytics Data Error</CardTitle>
          <CardDescription>
            Failed to load data from ThingSpeak. Please verify your
            VITE_THINGSPEAK_CHANNEL_ID in your .env file.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>IoT Sensor Analytics</CardTitle>
        <CardDescription>
          {isLoading
            ? "Loading data..."
            : "Real-time historical data from ThingSpeak sensors"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {chartData.length > 0 ? (
          <ChartContainer config={chartConfig} className="min-h-75 w-full">
            <LineChart
              accessibilityLayer
              data={chartData}
              margin={{
                left: -20,
                right: 12,
                top: 12,
                bottom: 12,
              }}
            >
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="time"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                fontSize={12}
              />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
              <Line
                dataKey="temperature"
                type="monotone"
                stroke="var(--color-temperature)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                dataKey="riskScore"
                type="monotone"
                stroke="var(--color-riskScore)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                dataKey="humidity"
                type="monotone"
                stroke="var(--color-humidity)"
                strokeWidth={2}
                dot={false}
              />
              <ChartLegend content={<ChartLegendContent />} />
            </LineChart>
          </ChartContainer>
        ) : (
          !isLoading && (
            <div className="flex min-h-75 items-center justify-center text-muted-foreground">
              No data available yet.
            </div>
          )
        )}
      </CardContent>
    </Card>
  )
}
