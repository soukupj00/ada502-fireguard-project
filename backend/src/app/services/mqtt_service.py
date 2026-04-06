import asyncio
import json
import logging

import paho.mqtt.client as mqtt

from config import settings

logger = logging.getLogger(__name__)


class MQTTService:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.host = settings.HIVEMQ_HOST
        self.port = settings.HIVEMQ_PORT
        self._connected = False

        if settings.HIVEMQ_USERNAME:
            self.client.username_pw_set(
                settings.HIVEMQ_USERNAME,
                settings.HIVEMQ_PASSWORD,
            )

        if settings.HIVEMQ_USE_TLS:
            self.client.tls_set(
                ca_certs=settings.HIVEMQ_CA_CERT,
                certfile=settings.HIVEMQ_CLIENT_CERT,
                keyfile=settings.HIVEMQ_CLIENT_KEY,
            )
            self.client.tls_insecure_set(settings.HIVEMQ_TLS_INSECURE)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            self._connected = True
        else:
            logger.error(f"Failed to connect to MQTT broker. Code: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning(f"Disconnected from MQTT broker. Code: {reason_code}")
        self._connected = False

    async def connect_async(self):
        """Asynchronously connect to the MQTT broker."""
        try:
            # Run the blocking connect in a thread pool so we don't block the event loop
            await asyncio.to_thread(self.client.connect, self.host, self.port)
            self.client.loop_start()  # Start the background thread for network traffic
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")

    def publish_alert(self, geohash: str, risk_level: str, risk_score: float):
        """Publishes a fire risk alert for a specific geohash."""
        if not self._connected:
            logger.warning("MQTT client not connected. Alert not sent.")
            return

        topic = f"fireguard/alerts/{geohash}"
        payload = {
            "level": risk_level,
            "score": risk_score,
            "message": f"High fire risk detected in {geohash}.",
        }

        try:
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            result.wait_for_publish()  # Wait for confirmation for QoS 1
            logger.info(f"Published alert to {topic}: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish MQTT message to {topic}: {e}")

    def stop(self):
        """Stops the MQTT client loop and disconnects."""
        self.client.loop_stop()
        self.client.disconnect()


# Singleton instance
mqtt_client = MQTTService()
