import logging
import time
from collections.abc import Callable, Iterator
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import Engine, Table
from sqlalchemy.exc import SQLAlchemyError

from sungrow_collector.client import ReauthorizationRequired, SungrowClient, SungrowError
from sungrow_collector.config import ConfigError, Settings
from sungrow_collector.mapping import (
    INVERTER_DEVICE_TYPE,
    POINT_ID_LIST,
    POINTS_PARAM,
    format_timestamp,
    to_reading,
)
from sungrow_collector.storage import upsert_readings

logger = logging.getLogger(__name__)

SOURCE = "cloud"
DEVICE_LIST_PATH = "/openapi/platform/getDeviceListByPsId"
REAL_TIME_PATH = "/openapi/platform/getDeviceRealTimeData"
MINUTE_HISTORY_PATH = "/openapi/platform/getDevicePointMinuteDataList"
HISTORY_WINDOW = timedelta(hours=3)
WINDOWS_PER_DAY = 8
DEVICE_LIST_PAGE_SIZE = 50


def day_windows(day: date, tz: ZoneInfo) -> Iterator[tuple[str, str]]:
    midnight = datetime(day.year, day.month, day.day, tzinfo=tz)
    for index in range(WINDOWS_PER_DAY):
        start = midnight + HISTORY_WINDOW * index
        end = start + HISTORY_WINDOW - timedelta(seconds=1)
        yield format_timestamp(start), format_timestamp(end)


class Collector:
    def __init__(self, settings: Settings, client: SungrowClient, engine: Engine, table: Table) -> None:
        if settings.system_id is None:
            raise ConfigError("SOLARSENSE_SYSTEM_ID is required to store readings")
        self._settings = settings
        self._system_id = settings.system_id
        self._client = client
        self._engine = engine
        self._table = table
        self._ps_key = settings.ps_key

    def today(self) -> date:
        return datetime.now(self._settings.plant_timezone).date()

    def poll_once(self) -> int:
        ps_key = self._resolve_ps_key()
        result = self._client.post(
            REAL_TIME_PATH,
            {"device_type": INVERTER_DEVICE_TYPE, "ps_key_list": [ps_key], "point_id_list": POINT_ID_LIST},
        )
        if ps_key in (result.get("illegal_ps_key_list") or result.get("fail_ps_key_list") or []):
            raise SungrowError("illegal_ps_key", f"{ps_key} is not available for this authorization")
        raw_points = [item.get("device_point", item) for item in result.get("device_point_list") or []]
        return self._store(raw_points)

    def backfill(self, start: date, end: date) -> int:
        today = self.today()
        if end >= today:
            logger.warning(
                "history never includes the current day: clamping end to %s", today - timedelta(days=1)
            )
            end = today - timedelta(days=1)
        ps_key = self._resolve_ps_key()
        total = 0
        day = start
        while day <= end:
            stored = 0
            for window_start, window_end in day_windows(day, self._settings.plant_timezone):
                result = self._client.post(
                    MINUTE_HISTORY_PATH,
                    {
                        "ps_key_list": [ps_key],
                        "points": POINTS_PARAM,
                        "start_time_stamp": window_start,
                        "end_time_stamp": window_end,
                        "is_get_point_dict": "0",
                    },
                )
                stored += self._store(result.get(ps_key) or [])
            logger.info("backfill %s: %d readings", day, stored)
            total += stored
            day += timedelta(days=1)
        return total

    def _store(self, raw_points: list[dict[str, Any]]) -> int:
        readings = [
            reading
            for raw in raw_points
            if (reading := to_reading(raw, self._settings.plant_timezone)) is not None
        ]
        return upsert_readings(
            self._engine, self._table, system_id=self._system_id, source=SOURCE, readings=readings
        )

    def _resolve_ps_key(self) -> str:
        if self._ps_key:
            return self._ps_key
        ps_id = self._settings.ps_id or self._single_authorized_ps_id()
        result = self._client.post(
            DEVICE_LIST_PATH,
            {
                "ps_id": ps_id,
                "device_type_list": [INVERTER_DEVICE_TYPE],
                "page": 1,
                "size": DEVICE_LIST_PAGE_SIZE,
            },
        )
        inverters = [
            device
            for device in result.get("pageList") or []
            if device.get("device_type") == INVERTER_DEVICE_TYPE
        ]
        if len(inverters) != 1:
            raise ConfigError(
                f"found {len(inverters)} inverters in plant {ps_id}: set SUNGROW_PS_KEY explicitly"
            )
        self._ps_key = str(inverters[0]["ps_key"])
        logger.info("using inverter ps_key %s", self._ps_key)
        return self._ps_key

    def _single_authorized_ps_id(self) -> str:
        ps_ids = self._client.known_ps_ids()
        if len(ps_ids) != 1:
            raise ConfigError(f"{len(ps_ids)} authorized plants found: set SUNGROW_PS_ID explicitly")
        return ps_ids[0]


def run_forever(
    collector: Collector,
    interval_seconds: int,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    backfilled: date | None = None
    while True:
        yesterday = collector.today() - timedelta(days=1)
        if backfilled != yesterday:
            try:
                collector.backfill(yesterday, yesterday)
                backfilled = yesterday
            except ReauthorizationRequired:
                raise
            except (SungrowError, httpx.HTTPError, SQLAlchemyError):
                logger.exception("backfill of %s failed, will retry in %ds", yesterday, interval_seconds)
        try:
            logger.info("poll stored %d reading(s)", collector.poll_once())
        except ReauthorizationRequired:
            raise
        except (SungrowError, httpx.HTTPError, SQLAlchemyError):
            logger.exception("poll failed, will retry in %ds", interval_seconds)
        sleep(interval_seconds)
