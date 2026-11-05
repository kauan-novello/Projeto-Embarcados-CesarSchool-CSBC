import argparse

import pandas as pd
from sqlalchemy import text

from db import (
    add_system_id_argument,
    get_engine,
    load_inverter_yield,
    load_max_ac_power_kw,
    load_weather_readings,
    load_weather_station_id,
)
from features import (
    LOCAL_TZ,
    TARGET_COLUMN,
    clean_energy_hours,
    fill_counter_gaps,
    fill_night_radiation,
    fill_saturated_humidity,
    hourly_energy,
)

COLUMNS = [
    TARGET_COLUMN,
    "energy_estimated",
    "radiation_wh_m2",
    "air_temp_c",
    "humidity_pct",
    "humidity_estimated",
    "pressure_hpa",
    "wind_speed_m_s",
]

INSERT = text(
    """
    INSERT INTO plant_hourly (system_id, hour_start, energy_wh, energy_estimated, radiation_wh_m2,
                              air_temp_c, humidity_pct, humidity_estimated, pressure_hpa,
                              wind_speed_m_s)
    VALUES (:system_id, :hour_start, :energy_wh, :energy_estimated, :radiation_wh_m2,
            :air_temp_c, :humidity_pct, :humidity_estimated, :pressure_hpa, :wind_speed_m_s)
    """
)


def build_plant_hourly(system_id: str) -> pd.DataFrame:
    max_ac_kw = load_max_ac_power_kw(system_id)
    energy = hourly_energy(load_inverter_yield(system_id), max_ac_kw)
    weather = load_weather_readings(load_weather_station_id(system_id))
    energy, estimated = fill_counter_gaps(
        load_inverter_yield(system_id, counter="daily_yield_wh"), energy, weather["radiation_wh_m2"], max_ac_kw
    )

    df = clean_energy_hours(weather.join(energy.to_frame().assign(energy_estimated=estimated), how="inner"))
    df["radiation_wh_m2"] = fill_night_radiation(df["radiation_wh_m2"])
    df["humidity_pct"], df["humidity_estimated"] = fill_saturated_humidity(df["humidity_pct"])
    return df[COLUMNS].dropna()


def save_plant_hourly(system_id: str, df: pd.DataFrame) -> None:
    rows = [
        {"system_id": system_id, "hour_start": hour.to_pydatetime(), **row}
        for hour, row in df.astype(object).iterrows()
    ]
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM plant_hourly WHERE system_id = :id"), {"id": system_id})
        conn.execute(INSERT, rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the clean hourly plant table")
    add_system_id_argument(parser)
    args = parser.parse_args()
    df = build_plant_hourly(args.system_id)
    save_plant_hourly(args.system_id, df)
    local = df.index.tz_convert(LOCAL_TZ)
    print(
        f"{len(df)} horas gravadas ({local.min():%d/%m/%Y} a {local.max():%d/%m/%Y}), "
        f"energia reconstruída em {int(df['energy_estimated'].sum())} (buracos de conexão)"
    )


if __name__ == "__main__":
    main()
