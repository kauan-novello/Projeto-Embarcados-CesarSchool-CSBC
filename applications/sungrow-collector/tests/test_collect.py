from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select

from sungrow_collector.client import SungrowError
from sungrow_collector.collect import (
    DEVICE_LIST_PATH,
    MINUTE_HISTORY_PATH,
    REAL_TIME_PATH,
    Collector,
    day_windows,
    run_forever,
)
from sungrow_collector.config import ConfigError

RECIFE = ZoneInfo("America/Recife")
PS_KEY = "700001_1_1_1"


class FakeClient:
    def __init__(self, responses: dict[str, Any], ps_ids: tuple[str, ...] = ("700001",)) -> None:
        self.responses = responses
        self.ps_ids = ps_ids
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def known_ps_ids(self) -> tuple[str, ...]:
        return self.ps_ids

    def post(self, path: str, body: dict[str, Any]) -> Any:
        self.calls.append((path, body))
        return self.responses[path]


def _device_list(*devices: dict[str, Any]) -> dict[str, Any]:
    return {"pageList": list(devices)}


def _count(engine, table) -> int:
    with engine.connect() as connection:
        return connection.execute(select(func.count()).select_from(table)).scalar_one()


def test_day_windows_cover_the_whole_local_day_in_three_hour_slices():
    windows = list(day_windows(date(2026, 11, 3), RECIFE))
    assert len(windows) == 8
    assert windows[0] == ("20261103000000", "20261103025959")
    assert windows[-1] == ("20261103210000", "20261103235959")


def test_poll_once_discovers_inverter_and_stores_reading(settings, engine, table):
    client = FakeClient(
        {
            DEVICE_LIST_PATH: _device_list(
                {"device_type": 1, "ps_key": PS_KEY}, {"device_type": 22, "ps_key": "x"}
            ),
            REAL_TIME_PATH: {
                "device_point_list": [
                    {"device_point": {"ps_key": PS_KEY, "device_time": "20261104101000", "p24": "23400.0"}}
                ]
            },
        }
    )

    stored = Collector(settings, client, engine, table).poll_once()  # type: ignore[arg-type]

    assert stored == 1
    assert _count(engine, table) == 1
    assert client.calls[0][1]["ps_id"] == "700001"
    assert client.calls[1][1]["ps_key_list"] == [PS_KEY]
    assert client.calls[1][1]["device_type"] == 1


def test_poll_twice_with_same_device_time_does_not_duplicate(settings, engine, table):
    point = {"device_point_list": [{"device_point": {"device_time": "20261104101000", "p24": "1"}}]}
    client = FakeClient(
        {DEVICE_LIST_PATH: _device_list({"device_type": 1, "ps_key": PS_KEY}), REAL_TIME_PATH: point}
    )
    collector = Collector(settings, client, engine, table)  # type: ignore[arg-type]

    collector.poll_once()
    collector.poll_once()

    assert _count(engine, table) == 1
    assert [path for path, _ in client.calls].count(DEVICE_LIST_PATH) == 1


def test_several_inverters_require_explicit_ps_key(settings, engine, table):
    client = FakeClient(
        {DEVICE_LIST_PATH: _device_list({"device_type": 1, "ps_key": "a"}, {"device_type": 1, "ps_key": "b"})}
    )
    with pytest.raises(ConfigError, match="SUNGROW_PS_KEY"):
        Collector(settings, client, engine, table).poll_once()  # type: ignore[arg-type]


def test_several_authorized_plants_require_explicit_ps_id(settings, engine, table):
    client = FakeClient({}, ps_ids=("1", "2"))
    with pytest.raises(ConfigError, match="SUNGROW_PS_ID"):
        Collector(settings, client, engine, table).poll_once()  # type: ignore[arg-type]


def test_unavailable_ps_key_is_reported(settings, engine, table):
    client = FakeClient(
        {
            DEVICE_LIST_PATH: _device_list({"device_type": 1, "ps_key": PS_KEY}),
            REAL_TIME_PATH: {"device_point_list": [], "fail_ps_key_list": [PS_KEY]},
        }
    )
    with pytest.raises(SungrowError, match="illegal_ps_key"):
        Collector(settings, client, engine, table).poll_once()  # type: ignore[arg-type]


def test_backfill_queries_eight_windows_per_day_and_clamps_today(settings, engine, table):
    yesterday = datetime.now(RECIFE).date() - timedelta(days=1)
    client = FakeClient(
        {
            DEVICE_LIST_PATH: _device_list({"device_type": 1, "ps_key": PS_KEY}),
            MINUTE_HISTORY_PATH: {PS_KEY: [{"time_stamp": "20261103120500", "p24": "30000"}]},
        }
    )
    collector = Collector(settings, client, engine, table)  # type: ignore[arg-type]

    stored = collector.backfill(yesterday, yesterday + timedelta(days=5))

    history_calls = [body for path, body in client.calls if path == MINUTE_HISTORY_PATH]
    assert len(history_calls) == 8
    assert history_calls[0]["start_time_stamp"].startswith(yesterday.strftime("%Y%m%d"))
    assert stored == 8
    assert _count(engine, table) == 1


class FakeLoopCollector:
    def __init__(self, days: list[date], fail_first_backfill: bool = False) -> None:
        self.days = days
        self.fail_first_backfill = fail_first_backfill
        self.backfills: list[date] = []
        self.polls = 0

    def today(self) -> date:
        return self.days[min(self.polls, len(self.days) - 1)]

    def backfill(self, start: date, end: date) -> int:
        if self.fail_first_backfill:
            self.fail_first_backfill = False
            raise SungrowError("E900", "temporary")
        self.backfills.append(start)
        return 0

    def poll_once(self) -> int:
        self.polls += 1
        return 1


class StopLoop(Exception):
    pass


def _run(collector: FakeLoopCollector, loops: int) -> None:
    calls = {"n": 0}

    def sleep(_: float) -> None:
        calls["n"] += 1
        if calls["n"] >= loops:
            raise StopLoop

    with pytest.raises(StopLoop):
        run_forever(collector, 300, sleep=sleep)  # type: ignore[arg-type]


def test_loop_backfills_yesterday_once_per_day():
    collector = FakeLoopCollector([date(2026, 11, 10)] * 3 + [date(2026, 11, 11)] * 2)
    _run(collector, 5)
    assert collector.backfills == [date(2026, 11, 9), date(2026, 11, 10)]
    assert collector.polls == 5


def test_loop_retries_a_failed_backfill_next_round():
    collector = FakeLoopCollector([date(2026, 11, 10)] * 3, fail_first_backfill=True)
    _run(collector, 3)
    assert collector.backfills == [date(2026, 11, 9)]
