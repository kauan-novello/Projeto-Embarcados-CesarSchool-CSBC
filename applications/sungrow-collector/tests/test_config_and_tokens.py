import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sungrow_collector.config import ConfigError, load_settings
from sungrow_collector.tokens import Tokens, TokenStore

BASE_ENV = {
    "SUNGROW_APPKEY": "a",
    "SUNGROW_SECRET_KEY": "s",
    "DATABASE_URL": "sqlite://",
    "SOLARSENSE_SYSTEM_ID": "11111111-1111-1111-1111-111111111111",
}


def test_interval_below_five_minutes_is_rejected():
    with pytest.raises(ConfigError, match="POLL_INTERVAL_SECONDS"):
        load_settings({**BASE_ENV, "POLL_INTERVAL_SECONDS": "60"})


def test_invalid_system_id_is_rejected():
    with pytest.raises(ConfigError, match="SOLARSENSE_SYSTEM_ID"):
        load_settings({**BASE_ENV, "SOLARSENSE_SYSTEM_ID": "not-a-uuid"})


def test_authorize_does_not_need_database_settings():
    env = {"SUNGROW_APPKEY": "a", "SUNGROW_SECRET_KEY": "s"}
    settings = load_settings(env, need_database=False)
    assert settings.system_id is None
    assert settings.redirect_uri == "https://localhost/callback"
    assert settings.plant_timezone.key == "America/Recife"


def test_missing_credentials_are_reported_by_name():
    with pytest.raises(ConfigError, match="SUNGROW_APPKEY"):
        load_settings({"SUNGROW_SECRET_KEY": "s"}, need_database=False)


def test_token_roundtrip_and_private_file_mode(tmp_path: Path):
    store = TokenStore(tmp_path / "state" / "tokens.json")
    tokens = Tokens("a", "r", datetime(2026, 11, 6, tzinfo=UTC), ("1", "2"))
    store.save(tokens)
    assert store.load() == tokens
    assert stat.S_IMODE((tmp_path / "state" / "tokens.json").stat().st_mode) == 0o600


def test_load_returns_none_without_file(tmp_path: Path):
    assert TokenStore(tmp_path / "missing.json").load() is None


def test_is_expiring_uses_safety_margin():
    now = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
    assert Tokens("a", "r", now + timedelta(minutes=5), ()).is_expiring(now)
    assert not Tokens("a", "r", now + timedelta(hours=1), ()).is_expiring(now)
