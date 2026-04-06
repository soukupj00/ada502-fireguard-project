from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Manages application settings and configurations."""

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/fireguard"
    REDIS_URL: str = "redis://localhost:6379/0"

    # HiveMQ MQTT Broker Settings
    HIVEMQ_HOST: str = "hivemq"  # Default to the service name in docker-compose
    HIVEMQ_PORT: int = 1883  # Standard MQTT port
    HIVEMQ_USERNAME: str | None = None
    HIVEMQ_PASSWORD: str | None = None
    HIVEMQ_USE_TLS: bool = False
    HIVEMQ_CA_CERT: str | None = None
    HIVEMQ_CLIENT_CERT: str | None = None
    HIVEMQ_CLIENT_KEY: str | None = None
    HIVEMQ_TLS_INSECURE: bool = False

    # ThingSpeak API Settings
    THINGSPEAK_WRITE_API_KEY: str = ""  # ThingSpeak Write API Key
    THINGSPEAK_CHANNEL_ID: str | None = None
    THINGSPEAK_BACKFILL_ON_STARTUP: bool = False

    # Testing Settings
    MQTT_TEST_MODE: bool = False  # Enable 30s interval MQTT push for testing
    THINGSPEAK_TEST_MODE: bool = (
        False  # Enable 1min interval ThingSpeak push for testing
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
