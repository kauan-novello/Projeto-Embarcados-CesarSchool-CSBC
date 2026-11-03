from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

INVERTER_DEVICE_TYPE = 1
TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
TIME_KEYS = ("device_time", "time_stamp")

POINT_COLUMNS: dict[int, str] = {
    24: "power_w",
    14: "dc_power_w",
    1: "daily_yield_wh",
    2: "total_yield_wh",
    4: "internal_temp_c",
    27: "grid_frequency_hz",
    29: "status_code",
    5: "mppt1_voltage_v",
    6: "mppt1_current_a",
    7: "mppt2_voltage_v",
    8: "mppt2_current_a",
    9: "mppt3_voltage_v",
    10: "mppt3_current_a",
    45: "mppt4_voltage_v",
    46: "mppt4_current_a",
}
MEASUREMENT_COLUMNS = tuple(POINT_COLUMNS.values())
POINT_ID_LIST = [str(point_id) for point_id in POINT_COLUMNS]
POINTS_PARAM = ",".join(f"p{point_id}" for point_id in POINT_COLUMNS)


def parse_timestamp(value: str, tz: ZoneInfo) -> datetime:
    return datetime.strptime(value, TIMESTAMP_FORMAT).replace(tzinfo=tz).astimezone(UTC)


def format_timestamp(value: datetime) -> str:
    return value.strftime(TIMESTAMP_FORMAT)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_reading(raw: Mapping[str, Any], tz: ZoneInfo) -> dict[str, Any] | None:
    time_value = next((raw[key] for key in TIME_KEYS if raw.get(key)), None)
    if time_value is None:
        return None
    measurements: dict[str, Any] = {}
    for point_id, column in POINT_COLUMNS.items():
        number = _to_float(raw.get(f"p{point_id}"))
        measurements[column] = int(number) if number is not None and column == "status_code" else number
    if all(value is None for value in measurements.values()):
        return None
    return {"recorded_at": parse_timestamp(str(time_value), tz), **measurements}
