import { useEffect, useRef } from "react"
import mqtt from "mqtt"
import { toast } from "sonner"
import { MQTT_BROKER_URL, MQTT_PASSWORD, MQTT_USERNAME } from "@/lib/env"
import type { MapFeature } from "@/types/map"

export function useMqttAlerts(subscriptions: MapFeature[] | undefined) {
  const clientRef = useRef<mqtt.MqttClient | null>(null)

  useEffect(() => {
    // 1. Connect to the HiveMQ Broker
    // We use the WebSocket URL defined in our env
    const client = mqtt.connect(MQTT_BROKER_URL, {
      connectTimeout: 10000,
      reconnectPeriod: 5000,
      ...(MQTT_USERNAME ? { username: MQTT_USERNAME } : {}),
      ...(MQTT_PASSWORD ? { password: MQTT_PASSWORD } : {}),
    })
    clientRef.current = client

    client.on("connect", () => {
      console.log("Connected to HiveMQ broker for real-time alerts")

      // Subscribe to topics for each of the user's subscriptions
      if (subscriptions && subscriptions.length > 0) {
        subscriptions.forEach((sub) => {
          // Assuming geohash is used as the zone identifier in the topic
          const geohash = sub.id.replace("sub-", "")
          const topic = `fireguard/alerts/${geohash}`
          client.subscribe(topic, (err) => {
            if (err) {
              console.error(`Failed to subscribe to ${topic}`, err)
            } else {
              console.log(`Subscribed to real-time alerts for zone: ${geohash}`)
            }
          })
        })
      }
    })

    // 2. Listen for incoming messages
    client.on("message", (topic, message) => {
      // The topic is usually like 'fireguard/alerts/u4pruyd'
      const geohash = topic.split("/").pop()
      const payloadString = message.toString()

      let alertMsg = `Risk escalated in zone: ${geohash}`

      try {
        // Try parsing as JSON in case the backend sends structured data
        const payload = JSON.parse(payloadString)
        if (payload.message) {
          alertMsg = payload.message
        } else if (payload.risk_score) {
          alertMsg = `Zone ${geohash} risk score increased to ${payload.risk_score}!`
        }
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
      } catch (e) {
        // If it's just a plain string, use it directly if it's not empty
        if (payloadString.trim().length > 0) {
          alertMsg = payloadString
        }
      }

      // 3. Trigger a red toast notification
      toast.error("🔥 Fire Risk Alert!", {
        description: alertMsg,
        duration: 8000,
      })
    })

    client.on("error", (err) => {
      console.error("MQTT Connection Error:", err)
      client.end()
    })

    // 4. Cleanup on unmount or when subscriptions change
    return () => {
      if (clientRef.current) {
        clientRef.current.end()
      }
    }
  }, [subscriptions]) // Re-run this effect if the user's subscriptions change
}
