from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine

from sungrow_collector.mapping import parse_timestamp, to_reading
from sungrow_collector.storage import StorageError, reflect_readings_table, upsert_readings
from tests.conftest import SYSTEM_ID

RECIFE = ZoneInfo("America/Recife")


def test_plant_local_time_is_converted_to_utc():
    assert parse_timestamp("20260511120000", RECIFE) == datetime(2026, 5, 11, 15, 0, tzinfo=UTC)


def test_realtime_point_is_mapped_to_columns_with_numeric_types():
    reading = to_reading(
        {
            "device_time": "20261104101000",
            "p24": "23400.0",
            "p14": "24800",
            "p1": "60800.0",
            "p29": "0.0",
            "p5": "474.9",
            "p46": "",
            "ps_key": "700001_1_1_1",
        },
        RECIFE,
    )
    assert reading is not None
    assert reading["recorded_at"] == datetime(2026, 11, 4, 13, 10, tzinfo=UTC)
    assert reading["power_w"] == 23400.0
    assert reading["status_code"] == 0
    assert isinstance(reading["status_code"], int)
    assert reading["mppt1_voltage_v"] == 474.9
    assert reading["mppt4_current_a"] is None
    assert reading["total_yield_wh"] is None


def test_history_rows_use_time_stamp_key():
    reading = to_reading({"time_stamp": "20261103120500", "p24": "30000"}, RECIFE)
    assert reading is not None
    assert reading["recorded_at"] == datetime(2026, 11, 3, 15, 5, tzinfo=UTC)


def test_rows_without_any_measurement_or_time_are_dropped():
    assert to_reading({"device_time": "20261104101000", "p24": "", "p1": None}, RECIFE) is None
    assert to_reading({"p24": "1"}, RECIFE) is None


def _reading(minute: int, **values):
    return {"recorded_at": datetime(2026, 11, 4, 13, minute, tzinfo=UTC), "power_w": 100.0, **values}


def _rows(engine: Engine, table):
    with engine.connect() as connection:
        return (
            connection.execute(select(table).order_by(table.c.recorded_at, table.c.source)).mappings().all()
        )


def test_upsert_is_idempotent_and_updates_existing_row(engine, table):
    upsert_readings(engine, table, system_id=SYSTEM_ID, source="cloud", readings=[_reading(0), _reading(5)])
    upsert_readings(
        engine,
        table,
        system_id=SYSTEM_ID,
        source="cloud",
        readings=[_reading(5, power_w=999.0), _reading(10)],
    )

    rows = _rows(engine, table)
    assert [row["power_w"] for row in rows] == [100.0, 999.0, 100.0]


def test_same_timestamp_from_another_source_is_a_separate_row(engine, table):
    upsert_readings(engine, table, system_id=SYSTEM_ID, source="cloud", readings=[_reading(0)])
    upsert_readings(engine, table, system_id=SYSTEM_ID, source="modbus", readings=[_reading(0)])

    assert [row["source"] for row in _rows(engine, table)] == ["cloud", "modbus"]


def test_upsert_of_nothing_is_a_noop(engine, table):
    assert upsert_readings(engine, table, system_id=SYSTEM_ID, source="cloud", readings=[]) == 0


def test_missing_table_gives_actionable_error():
    from sqlalchemy import create_engine

    with pytest.raises(StorageError, match="alembic upgrade head"):
        reflect_readings_table(create_engine("sqlite://"))
