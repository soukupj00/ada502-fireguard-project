from config import Settings


def test_settings_disable_backfill_and_mqtt_by_default():
    settings = Settings()

    assert settings.THINGSPEAK_BACKFILL_ON_STARTUP is False
    assert settings.MQTT_TEST_MODE is False


def test_settings_explicit_true_values_are_respected(monkeypatch):
    monkeypatch.setenv("THINGSPEAK_BACKFILL_ON_STARTUP", "true")
    monkeypatch.setenv("MQTT_TEST_MODE", "true")

    settings = Settings()

    assert settings.THINGSPEAK_BACKFILL_ON_STARTUP is True
    assert settings.MQTT_TEST_MODE is True
