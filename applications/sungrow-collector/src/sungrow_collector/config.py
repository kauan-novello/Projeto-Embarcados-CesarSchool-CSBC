from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MIN_POLL_INTERVAL_SECONDS = 300


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    appkey: str
    secret_key: str
    redirect_uri: str
    gateway_url: str
    ps_id: str | None
    ps_key: str | None
    plant_timezone: ZoneInfo
    poll_interval_seconds: int
    token_file: Path
    database_url: str | None
    system_id: UUID | None


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ConfigError(f"missing required setting {name}")
    return value


def _optional(env: Mapping[str, str], name: str) -> str | None:
    return env.get(name, "").strip() or None


def _parse_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ConfigError(f"unknown PLANT_TIMEZONE {name!r}") from exc


def _parse_interval(raw: str) -> int:
    try:
        interval = int(raw)
    except ValueError as exc:
        raise ConfigError(f"POLL_INTERVAL_SECONDS must be an integer, got {raw!r}") from exc
    if interval < MIN_POLL_INTERVAL_SECONDS:
        raise ConfigError(
            f"POLL_INTERVAL_SECONDS must be >= {MIN_POLL_INTERVAL_SECONDS} "
            "(the API only refreshes about every 5 minutes)"
        )
    return interval


def _parse_system_id(raw: str) -> UUID:
    try:
        return UUID(raw)
    except ValueError as exc:
        raise ConfigError(f"SOLARSENSE_SYSTEM_ID is not a valid UUID: {raw!r}") from exc


def load_settings(env: Mapping[str, str], *, need_database: bool = True) -> Settings:
    return Settings(
        appkey=_required(env, "SUNGROW_APPKEY"),
        secret_key=_required(env, "SUNGROW_SECRET_KEY"),
        redirect_uri=env.get("SUNGROW_REDIRECT_URI", "").strip() or "https://localhost/callback",
        gateway_url=(
            env.get("SUNGROW_GATEWAY_URL", "").strip() or "https://gateway.isolarcloud.com.hk"
        ).rstrip("/"),
        ps_id=_optional(env, "SUNGROW_PS_ID"),
        ps_key=_optional(env, "SUNGROW_PS_KEY"),
        plant_timezone=_parse_timezone(env.get("PLANT_TIMEZONE", "").strip() or "America/Recife"),
        poll_interval_seconds=_parse_interval(env.get("POLL_INTERVAL_SECONDS", "").strip() or "300"),
        token_file=Path(env.get("TOKEN_FILE", "").strip() or ".state/tokens.json"),
        database_url=_required(env, "DATABASE_URL") if need_database else None,
        system_id=_parse_system_id(_required(env, "SOLARSENSE_SYSTEM_ID")) if need_database else None,
    )
