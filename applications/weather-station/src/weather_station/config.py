import re
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_DEVICE_ID = "02534F4C4152"
DEVICE_ID_PATTERN = re.compile(r"[0-9A-F]{12}")


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    device_id: str
    latitude: float
    longitude: float
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    check_interval_seconds: int
    pairing_seconds: int
    pairing_publish_seconds: int


def _number(env: Mapping[str, str], name: str, default: str, cast: type) -> float | int:
    raw = env.get(name, "").strip() or default
    try:
        return cast(raw)  # type: ignore[no-any-return]
    except ValueError as exc:
        raise ConfigError(f"{name} must be a {cast.__name__}, got {raw!r}") from exc


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is required")
    return value


def load_settings(env: Mapping[str, str]) -> Settings:
    device_id = (env.get("DEVICE_ID", "").strip() or DEFAULT_DEVICE_ID).upper()
    if not DEVICE_ID_PATTERN.fullmatch(device_id):
        raise ConfigError(f"DEVICE_ID must be 12 hex characters like a MAC, got {device_id!r}")
    return Settings(
        device_id=device_id,
        latitude=float(_number(env, "LATITUDE", "-8.112", float)),
        longitude=float(_number(env, "LONGITUDE", "-35.015", float)),
        mqtt_host=env.get("MQTT_BROKER_HOST", "").strip() or "localhost",
        mqtt_port=int(_number(env, "MQTT_BROKER_PORT", "1883", int)),
        mqtt_username=_required(env, "MQTT_USERNAME"),
        mqtt_password=_required(env, "MQTT_PASSWORD"),
        check_interval_seconds=int(_number(env, "CHECK_INTERVAL_SECONDS", "300", int)),
        pairing_seconds=int(_number(env, "PAIRING_SECONDS", "0", int)),
        pairing_publish_seconds=int(_number(env, "PAIRING_PUBLISH_SECONDS", "5", int)),
    )
