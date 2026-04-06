"use client"

import { useMemo, useState } from "react"
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
import { Button } from "@/components/ui/button"
import { useThingspeakData } from "@/hooks/use-thingspeak-data"

// Line style patterns for visual distinction
const LINE_STYLES = [
  { dasharray: undefined, width: 2 }, // Solid
  { dasharray: "5 5", width: 2 }, // Dashed
  { dasharray: "2 4", width: 2 }, // Dotted
  { dasharray: "8 4", width: 2 }, // Long dash
  { dasharray: "5 2 2 2", width: 2 }, // Dash-dot
  { dasharray: "3 3 1 3", width: 2 }, // Dot-dash-dot
  { dasharray: "10 2", width: 2 }, // Long dash short gap
  { dasharray: undefined, width: 3 }, // Thick solid (National Average)
]

export function AnalyticsWidget() {
  const { data, isLoading, isError } = useThingspeakData(24) // Fetch last 24 results
  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set()) // Track selected fields

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
          color: `hsl(var(--chart-${(index % 8) + 1}))`, // Use all 8 chart colors
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

  // Calculate dynamic Y-axis domain with padding
  const yAxisDomain = useMemo(() => {
    if (chartData.length === 0) return [0, 100]

    // Get fields to display (all if none selected, else selected)
    const fieldsToCheck =
      selectedFields.size === 0
        ? Object.keys(chartConfig)
        : Array.from(selectedFields)

    // Find min and max values across visible data
    let minValue = Infinity
    let maxValue = -Infinity

    chartData.forEach((dataPoint) => {
      fieldsToCheck.forEach((fieldKey) => {
        const val = dataPoint[fieldKey]
        if (typeof val === "number" && !isNaN(val)) {
          minValue = Math.min(minValue, val)
          maxValue = Math.max(maxValue, val)
        }
      })
    })

    if (minValue === Infinity || maxValue === -Infinity) {
      return [0, 100]
    }

    // Add padding: 10% of the range on each side
    const range = maxValue - minValue
    const padding = range * 0.1
    const min = Math.max(0, Math.floor((minValue - padding) * 2) / 2) // Round down to nearest 0.5
    const max = Math.ceil((maxValue + padding) * 2) / 2 // Round up to nearest 0.5

    return [min, max]
  }, [chartData, chartConfig, selectedFields])

  // Determine which fields to display
  const activeFields =
    selectedFields.size === 0
      ? Object.keys(chartConfig)
      : Array.from(selectedFields)

  // Handle field button click
  const handleFieldToggle = (fieldKey: string) => {
    const newSelected = new Set(selectedFields)

    if (newSelected.has(fieldKey)) {
      newSelected.delete(fieldKey)
    } else {
      newSelected.add(fieldKey)
    }

    setSelectedFields(newSelected)
  }

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
        {/* City/Region Toggle Buttons */}
        <div className="mb-6 flex flex-wrap gap-2">
          <Button
            variant={selectedFields.size === 0 ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedFields(new Set())}
            className="cursor-pointer"
          >
            See All
          </Button>

          {Object.entries(chartConfig).map(([fieldKey, config]) => (
            <Button
              key={fieldKey}
              variant={selectedFields.has(fieldKey) ? "default" : "outline"}
              size="sm"
              onClick={() => handleFieldToggle(fieldKey)}
              className="cursor-pointer"
            >
              {config.label}
            </Button>
          ))}
        </div>

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
                domain={yAxisDomain}
              />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />

              {/* Dynamically render a Line for every active field */}
              {activeFields.map((fieldKey, index) => {
                const lineStyle = LINE_STYLES[index % LINE_STYLES.length]
                return (
                  <Line
                    key={fieldKey}
                    dataKey={fieldKey}
                    type="monotone"
                    stroke={`var(--color-${fieldKey})`}
                    strokeWidth={lineStyle.width}
                    strokeDasharray={lineStyle.dasharray}
                    dot={false}
                  />
                )
              })}

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
