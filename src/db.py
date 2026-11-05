import argparse
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()

SYSTEM_ID_ENV = "SOLARSENSE_SYSTEM_ID"


def add_system_id_argument(parser: argparse.ArgumentParser) -> None:
    from_env = os.environ.get(SYSTEM_ID_ENV)
    parser.add_argument("--system-id", default=from_env, required=from_env is None)


def get_engine() -> Engine:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return create_engine(url)


YIELD_COUNTERS = ("total_yield_wh", "daily_yield_wh")


def load_inverter_yield(
    system_id: str, engine: Engine | None = None, counter: str = "total_yield_wh"
) -> pd.Series:
    if counter not in YIELD_COUNTERS:
        raise ValueError(f"counter must be one of {YIELD_COUNTERS}")
    engine = engine or get_engine()
    query = f"""
        SELECT recorded_at, {counter}
        FROM inverter_readings
        WHERE system_id = %(system_id)s AND {counter} IS NOT NULL
        ORDER BY recorded_at
    """
    df = pd.read_sql(query, engine, params={"system_id": system_id}, parse_dates=["recorded_at"])
    df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True)
    return df.drop_duplicates("recorded_at").set_index("recorded_at")[counter]


def load_weather_station_id(system_id: str, engine: Engine | None = None) -> str:
    engine = engine or get_engine()
    df = pd.read_sql(
        "SELECT weather_station_id FROM pv_systems WHERE id = %(system_id)s",
        engine,
        params={"system_id": system_id},
    )
    if df.empty or df["weather_station_id"].iloc[0] is None:
        raise ValueError(f"System {system_id} has no weather station")
    return str(df["weather_station_id"].iloc[0])


def load_weather_readings(station_id: str, engine: Engine | None = None) -> pd.DataFrame:
    engine = engine or get_engine()
    query = """
        SELECT hour_start, radiation_wh_m2, air_temp_c, humidity_pct, pressure_hpa, wind_speed_m_s
        FROM weather_readings
        WHERE station_id = %(station_id)s
        ORDER BY hour_start
    """
    df = pd.read_sql(query, engine, params={"station_id": station_id})
    df["hour_start"] = pd.to_datetime(df["hour_start"], utc=True)
    return df.set_index("hour_start")


def load_max_ac_power_kw(system_id: str, engine: Engine | None = None) -> float:
    engine = engine or get_engine()
    df = pd.read_sql(
        "SELECT max(power_w) AS max_w FROM inverter_readings WHERE system_id = %(system_id)s",
        engine,
        params={"system_id": system_id},
    )
    if df["max_w"].isna().iloc[0]:
        raise ValueError(f"System {system_id} has no inverter power readings")
    return float(df["max_w"].iloc[0]) / 1000.0


def load_installed_power_kw(system_id: str, engine: Engine | None = None) -> float:
    engine = engine or get_engine()
    df = pd.read_sql(
        "SELECT installed_power_kw FROM pv_systems WHERE id = %(system_id)s",
        engine,
        params={"system_id": system_id},
    )
    if df.empty:
        raise ValueError(f"System {system_id} not found")
    return float(df["installed_power_kw"].iloc[0])


def mark_model_active(system_id: str, engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE pv_systems SET status = 'MODEL_ACTIVE' WHERE id = :id"),
            {"id": system_id},
        )
