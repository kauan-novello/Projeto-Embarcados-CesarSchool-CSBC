import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from weather_station.config import ConfigError, load_settings
from weather_station.open_meteo import HourlyWeather, fetch_closed_hours
from weather_station.station import run

HOUR = datetime(2026, 11, 10, 14, 0, tzinfo=UTC)
ENV = {"MQTT_USERNAME": "device", "MQTT_PASSWORD": "device-password"}


def _weather(hour_start: datetime = HOUR) -> HourlyWeather:
    return HourlyWeather(
        hour_start, irradiance_w_m2=640.0, air_temp_c=29.1, humidity_pct=62.0, pressure_hpa=1008.4
    )


class FakePublisher:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict]] = []

    def publish(self, topic: str, payload: str) -> None:
        self.messages.append((topic, json.loads(payload)))


class StopLoop(Exception):
    pass


def _run(settings, fetch, loops: int) -> FakePublisher:
    publisher = FakePublisher()
    elapsed = {"t": 0.0, "n": 0}

    def sleep(seconds: float) -> None:
        elapsed["t"] += seconds
        elapsed["n"] += 1
        if elapsed["n"] >= loops:
            raise StopLoop

    with pytest.raises(StopLoop):
        run(settings, publisher, fetch, clock=lambda: elapsed["t"], sleep=sleep, now=lambda: HOUR)
    return publisher


def test_settings_default_to_a_mac_like_device_id():
    settings = load_settings(ENV)
    assert settings.device_id == "02534F4C4152"
    assert settings.check_interval_seconds == 300


@pytest.mark.parametrize("missing", ["MQTT_USERNAME", "MQTT_PASSWORD"])
def test_settings_require_the_broker_credentials(missing):
    env = {key: value for key, value in ENV.items() if key != missing}
    with pytest.raises(ConfigError, match=missing):
        load_settings(env)


def test_settings_reject_an_id_the_backend_would_discard():
    with pytest.raises(ConfigError):
        load_settings({**ENV, "DEVICE_ID": "open-meteo"})


def test_pairing_repeats_the_latest_hour_with_the_esp_payload():
    settings = load_settings({**ENV, "PAIRING_SECONDS": "10", "PAIRING_PUBLISH_SECONDS": "5"})
    publisher = _run(settings, lambda now: [_weather()], loops=2)

    assert [msg["pairing_mode"] for _, msg in publisher.messages] == [True, True]
    topic, payload = publisher.messages[0]
    assert topic == "solarsense/02534F4C4152/readings"
    assert payload == {
        "timestamp": HOUR.isoformat(),
        "irradiance": 640.0,
        "ambient_temp_c": 29.1,
        "ambient_humidity_pct": 62.0,
        "pressure_hpa": 1008.4,
        "pairing_mode": True,
    }


def test_each_closed_hour_is_published_once_and_missed_hours_are_caught_up():
    settings = load_settings({**ENV, "PAIRING_SECONDS": "0"})
    later = [HOUR + timedelta(hours=n) for n in range(4)]
    responses = iter([later[:2], later[:2], later])
    publisher = _run(settings, lambda now: [_weather(h) for h in next(responses)], loops=3)
    assert [msg["timestamp"] for _, msg in publisher.messages] == [
        later[1].isoformat(),
        later[2].isoformat(),
        later[3].isoformat(),
    ]


def test_failed_fetch_publishes_nothing_new():
    settings = load_settings({**ENV, "PAIRING_SECONDS": "0"})
    results = iter([[_weather()], httpx.ConnectError("offline")])

    def fetch(now: datetime) -> list[HourlyWeather]:
        result = next(results)
        if isinstance(result, Exception):
            raise result
        return result

    assert len(_run(settings, fetch, loops=2).messages) == 1


def test_fetch_keeps_closed_hours_stamped_by_their_start():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "hourly": {
                    "time": ["2026-11-10T14:00", "2026-11-10T15:00", "2026-11-10T16:00"],
                    "shortwave_radiation": [700, 640, 500],
                    "temperature_2m": [29.5, 29.1, 28.0],
                    "relative_humidity_2m": [60, 62, 66],
                    "surface_pressure": [1008.0, 1008.4, 1008.6],
                }
            },
        )

    now = datetime(2026, 11, 10, 15, 20, tzinfo=UTC)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        hours = fetch_closed_hours(client, -8.112, -35.015, now)
    assert [h.hour_start for h in hours] == [HOUR - timedelta(hours=1), HOUR]
    assert hours[-1] == _weather(HOUR)
