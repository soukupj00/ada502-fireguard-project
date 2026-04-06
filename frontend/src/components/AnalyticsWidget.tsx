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

export function AnalyticsWidget() {
  const { data, isLoading, isError } = useThingspeakData(24) // Fetch last 24 results

  // Dynamically build the chart configuration based on ThingSpeak channel metadata
  const chartConfig = useMemo(() => {
    const config: Record<string, { label: string; color: string }> = {}
    if (!data || !data.channel) return config

    // Map each field to a color from the Tailwind theme (chart-1 through chart-8)
    const fields = [
      { key: "field1", label: data.channel.field1 },
      { key: "field2", label: data.channel.field2 },
      { key: "field3", label: data.channel.field3 },
      { key: "field4", label: data.channel.field4 },
      { key: "field5", label: data.channel.field5 },
      { key: "field6", label: data.channel.field6 },
      { key: "field7", label: data.channel.field7 },
      { key: "field8", label: data.channel.field8 },
    ]

    fields.forEach((field, index) => {
      if (field.label) {
        config[field.key] = {
          label: field.label,
          color: `hsl(var(--chart-${(index % 5) + 1}))`, // Cycle through 5 standard chart colors
        }
      }
    })

    return config satisfies ChartConfig
  }, [data])

  // Dynamically parse the feed data to match the configured fields
  const chartData = useMemo(() => {
    if (!data || !data.feeds || !data.channel) return []

    return data.feeds.map((feed) => {
      // Base object with formatted time
      const dataPoint: Record<string, string | number | null> = {
        time: new Date(feed.created_at).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      }

      // Add data only for fields that have a name in the channel metadata
      for (let i = 1; i <= 8; i++) {
        const fieldKey = `field${i}` as keyof typeof feed
        const channelFieldKey = `field${i}` as keyof typeof data.channel

        if (data.channel[channelFieldKey]) {
          const val = feed[fieldKey]
          dataPoint[fieldKey] = val ? parseFloat(val as string) : null
        }
      }
      return dataPoint
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

  // Get the keys of the active fields to render the lines
  const activeFields = Object.keys(chartConfig)

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>
          {data?.channel?.name || "National Fire Risk Analytics"}
        </CardTitle>
        <CardDescription>
          {isLoading
            ? "Loading data..."
            : data?.channel?.description ||
              "Hourly Fire Risk Scores across Norway"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {chartData.length > 0 ? (
          <ChartContainer config={chartConfig} className="min-h-100 w-full">
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
                domain={[0, "dataMax + 10"]} // Add some padding to the top of the graph
              />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />

              {/* Dynamically render a Line for every active field */}
              {activeFields.map((fieldKey) => (
                <Line
                  key={fieldKey}
                  dataKey={fieldKey}
                  type="monotone"
                  stroke={`var(--color-${fieldKey})`}
                  strokeWidth={fieldKey === "field8" ? 3 : 2} // Make National Average (field8) thicker
                  dot={false}
                  // Make standard cities slightly dashed, and National average solid, or vice versa if you prefer
                  strokeDasharray={fieldKey !== "field8" ? "4 4" : undefined}
                />
              ))}

              <ChartLegend content={<ChartLegendContent />} />
            </LineChart>
          </ChartContainer>
        ) : (
          !isLoading && (
            <div className="flex min-h-100 items-center justify-center text-muted-foreground">
              No data available yet. Waiting for Intelligence System to publish.
            </div>
          )
        )}
      </CardContent>
    </Card>
  )
}
