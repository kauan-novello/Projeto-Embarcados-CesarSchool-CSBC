import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    create_engine,
)
from sqlalchemy.pool import StaticPool

from sungrow_collector.client import SungrowClient
from sungrow_collector.config import Settings, load_settings
from sungrow_collector.mapping import MEASUREMENT_COLUMNS
from sungrow_collector.storage import TABLE_NAME, reflect_readings_table
from sungrow_collector.tokens import Tokens, TokenStore

SYSTEM_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
FIXED_NOW = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return load_settings(
        {
            "SUNGROW_APPKEY": "appkey-1",
            "SUNGROW_SECRET_KEY": "secret-1",
            "DATABASE_URL": "sqlite://",
            "SOLARSENSE_SYSTEM_ID": str(SYSTEM_ID),
            "TOKEN_FILE": str(tmp_path / "tokens.json"),
        }
    )


@pytest.fixture()
def store(settings: Settings) -> TokenStore:
    return TokenStore(settings.token_file)


@pytest.fixture()
def valid_tokens(store: TokenStore) -> Tokens:
    tokens = Tokens("access-1", "refresh-1", FIXED_NOW.replace(year=2027), ("700001",))
    store.save(tokens)
    return tokens


@pytest.fixture()
def make_client(
    settings: Settings, store: TokenStore
) -> Callable[[Callable[[httpx.Request], httpx.Response]], SungrowClient]:
    def factory(handler: Callable[[httpx.Request], httpx.Response]) -> SungrowClient:
        http = httpx.Client(transport=httpx.MockTransport(handler))
        return SungrowClient(settings, store, http=http, now=lambda: FIXED_NOW, sleep=lambda _: None)

    return factory


@pytest.fixture()
def engine() -> Engine:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    columns: list[Column[Any]] = [
        Column("id", Uuid, primary_key=True),
        Column("system_id", Uuid, nullable=False),
        Column("recorded_at", DateTime(timezone=True), nullable=False),
        Column("source", String(16), nullable=False),
    ]
    columns += [Column(name, Integer if name == "status_code" else Float) for name in MEASUREMENT_COLUMNS]
    Table(
        TABLE_NAME,
        MetaData(),
        *columns,
        UniqueConstraint(
            "system_id", "recorded_at", "source", name="uq_inverter_readings_system_recorded_source"
        ),
    ).create(engine)
    return engine


@pytest.fixture()
def table(engine: Engine) -> Table:
    return reflect_readings_table(engine)
