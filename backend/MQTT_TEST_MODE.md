# MQTT Testing Mode

## Overview
The MQTT testing mode allows you to test MQTT connectivity and frontend message reception without waiting for the Intelligence System's hourly updates. When enabled, the backend will push all current fire risk data to MQTT every 30 seconds for all user subscriptions.

## How to Enable

### Option 1: Environment Variable
Set the environment variable when starting the backend:

```bash
# Docker Compose
docker compose -e MQTT_TEST_MODE=true up backend

# Direct Python
MQTT_TEST_MODE=true python -m uvicorn main:app --reload
```

### Option 2: Docker Compose File
Add to the backend service environment in `docker-compose.yml`:

```yaml
environment:
  MQTT_TEST_MODE: "true"
```

### Option 3: .env File
Add to your `.env` file:

```
MQTT_TEST_MODE=true
```

## How It Works

1. **Startup**: When the backend starts with `MQTT_TEST_MODE=true`, the MQTT test task is created.
2. **Every 30 seconds**:
   - Fetches all distinct geohashes that users have subscribed to
   - Retrieves the current fire risk data for each geohash
   - Publishes each risk update to MQTT using the same topic structure: `fireguard/alerts/{geohash}`
3. **No filtering**: Unlike production, it publishes ALL current risks regardless of risk level (not just High/Extreme)
4. **Shutdown**: The task is gracefully cancelled when the backend shuts down

## Testing Flow

1. Start the backend with `MQTT_TEST_MODE=true`
2. Frontend connects to the MQTT broker (HiveMQ WebSocket)
3. User subscribes to a location in the frontend
4. Within 30 seconds, MQTT messages should arrive with the current fire risk data
5. Frontend should receive and display the data

## Expected MQTT Topics

Messages are published to: `fireguard/alerts/{geohash}`

Example payload:
```json
{
  "level": "High",
  "score": 75.5,
  "message": "High fire risk detected in u4x4r."
}
```

## Troubleshooting

### No messages received?
- Check MQTT broker is running: `docker compose ps`
- Verify MQTT connection in backend logs: `docker compose logs backend | grep -i mqtt`
- Check frontend MQTT subscription in browser console
- Ensure user has at least one active subscription

### Messages every 30s but not changing?
- This is expected if the database doesn't have new data
- To test with changing data, update the database directly or restart the Intelligence System

## Production Note

⚠️ **Important**: Disable MQTT test mode in production by setting `MQTT_TEST_MODE=false` or removing it from environment.
This is only for development and testing purposes. In production, MQTT alerts should only be triggered by real Intelligence System events.
