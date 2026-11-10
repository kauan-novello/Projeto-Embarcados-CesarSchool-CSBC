import json
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

from weather_station.config import Settings
from weather_station.open_meteo import HourlyWeather

logger = logging.getLogger(__name__)


class Publisher(Protocol):
    def publish(self, topic: str, payload: str) -> Any: ...


def readings_topic(device_id: str) -> str:
    return f"solarsense/{device_id}/readings"


def to_payload(weather: HourlyWeather, *, pairing: bool) -> dict[str, Any]:
    return {
        "timestamp": weather.hour_start.isoformat(),
        "irradiance": weather.irradiance_w_m2,
        "ambient_temp_c": weather.air_temp_c,
        "ambient_humidity_pct": weather.humidity_pct,
        "pressure_hpa": weather.pressure_hpa,
        "pairing_mode": pairing,
    }


def run(
    settings: Settings,
    publisher: Publisher,
    fetch: Callable[[datetime], list[HourlyWeather]],
    *,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> None:
    started = clock()
    hours: list[HourlyWeather] = []
    published: datetime | None = None
    checked_at = float("-inf")
    topic = readings_topic(settings.device_id)
    while True:
        pairing = clock() - started < settings.pairing_seconds
        if clock() - checked_at >= settings.check_interval_seconds:
            try:
                hours = fetch(now())
                checked_at = clock()
            except (httpx.HTTPError, KeyError, ValueError):
                logger.exception("could not fetch the weather, will retry")
        if hours:
            if pairing or published is None:
                pending = hours[-1:]
            else:
                pending = [hour for hour in hours if hour.hour_start > published]
            for hour in pending:
                publisher.publish(topic, json.dumps(to_payload(hour, pairing=pairing)))
            published = hours[-1].hour_start
        sleep(settings.pairing_publish_seconds if pairing else settings.check_interval_seconds)
