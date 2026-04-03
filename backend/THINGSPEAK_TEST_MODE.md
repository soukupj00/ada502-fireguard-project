# ThingSpeak Test Mode - Reference Card

## Quick Commands

### Start with ThingSpeak Testing
```bash
THINGSPEAK_TEST_MODE=true docker compose up --build backend
```

### Start with Both MQTT + ThingSpeak Testing
```bash
MQTT_TEST_MODE=true THINGSPEAK_TEST_MODE=true docker compose up --build backend
```

### Monitor ThingSpeak Updates
```bash
docker compose logs -f backend | grep "ThingSpeak Test"
```

### Monitor Both Test Modes
```bash
docker compose logs -f backend | grep -E "MQTT Test|ThingSpeak Test"
```

---

## What Happens

**Every 60 seconds:**
1. Query analytics target zones (`is_analytics_target=true`)
2. Get current fire risk for each zone
3. Get latest weather data (temperature, humidity)
4. If values unchanged → apply random ±1 variation
5. Calculate national average risk
6. Push all data to ThingSpeak channel

---

## Data Pushed

- **Field 1-3:** Zone 1 (Temp, Humidity, Risk)
- **Field 4-6:** Zone 2 (Temp, Humidity, Risk)
- **Field 7:** National Average Risk
- **Field 8:** Available

---

## Key Features

✅ 60-second interval pushes
✅ Random value variation for graph visibility
✅ National average calculation
✅ Analytics targets only
✅ Error resilient
✅ Graceful shutdown
✅ Production-safe (disabled by default)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No ThingSpeak updates | Check `THINGSPEAK_TEST_MODE=true` is set |
| "No analytics target zones" | Mark zones as `is_analytics_target=true` in DB |
| API errors | Verify THINGSPEAK_WRITE_API_KEY in .env |
| Backend won't start | Check logs: `docker compose logs backend` |

---

## Testing Workflow

1. `THINGSPEAK_TEST_MODE=true docker compose up --build backend`
2. Wait for "Starting 1-minute interval push..." message
3. Open ThingSpeak channel dashboard
4. Watch field values update every 60 seconds
5. Verify values change slightly (±1 variation)
6. Disable test mode for production: Remove env var and restart

---

## Docker Compose Integration

Already configured in `docker-compose.yml`:
```yaml
environment:
  THINGSPEAK_TEST_MODE: ${THINGSPEAK_TEST_MODE:-false}
```

Just pass the environment variable when starting!
