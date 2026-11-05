import argparse
from datetime import UTC, datetime

from sqlalchemy import text

from db import get_engine
from weather import OPEN_METEO_SOURCE_ID, download_open_meteo, load_open_meteo_hourly

COLUMNS = ["radiation_wh_m2", "air_temp_c", "humidity_pct", "precipitation_mm", "pressure_hpa", "wind_speed_m_s"]

UPSERT = text(
    """
    INSERT INTO weather_readings (station_id, hour_start, radiation_wh_m2, air_temp_c, humidity_pct,
                                  precipitation_mm, pressure_hpa, wind_speed_m_s)
    VALUES (:station_id, :hour_start, :radiation_wh_m2, :air_temp_c, :humidity_pct,
            :precipitation_mm, :pressure_hpa, :wind_speed_m_s)
    ON CONFLICT (station_id, hour_start) DO UPDATE SET
        radiation_wh_m2 = EXCLUDED.radiation_wh_m2,
        air_temp_c = EXCLUDED.air_temp_c,
        humidity_pct = EXCLUDED.humidity_pct,
        precipitation_mm = EXCLUDED.precipitation_mm,
        pressure_hpa = EXCLUDED.pressure_hpa,
        wind_speed_m_s = EXCLUDED.wind_speed_m_s
    """
)


INVERTER_RANGE = text(
    """
    SELECT min(r.recorded_at), max(r.recorded_at)
    FROM inverter_readings r
    JOIN pv_systems s ON s.id = r.system_id
    WHERE s.weather_station_id = :station OR s.id = CAST(:system_id AS uuid)
    """
)


def load_weather(system_id: str | None = None) -> int:
    weather = load_open_meteo_hourly()[COLUMNS].dropna(how="all")
    with get_engine().connect() as conn:
        start, end = conn.execute(INVERTER_RANGE, {"station": OPEN_METEO_SOURCE_ID, "system_id": system_id}).one()
    if start is not None:
        weather = weather[(weather.index >= start) & (weather.index <= end)]
    rows = [
        {"station_id": OPEN_METEO_SOURCE_ID, "hour_start": hour.to_pydatetime(), **row}
        for hour, row in weather.astype(object).where(weather.notna(), None).iterrows()
    ]
    with get_engine().begin() as conn:
        conn.execute(UPSERT, rows)
        if system_id:
            conn.execute(
                text("UPDATE pv_systems SET weather_station_id = :station WHERE id = :id"),
                {"station": OPEN_METEO_SOURCE_ID, "id": system_id},
            )
    return len(rows)


def refresh_range(system_id: str | None) -> tuple[str, str]:
    with get_engine().connect() as conn:
        start, _ = conn.execute(INVERTER_RANGE, {"station": OPEN_METEO_SOURCE_ID, "system_id": system_id}).one()
    if start is None:
        raise SystemExit("no inverter readings to align the weather with")
    return f"{start:%Y-%m-%d}", f"{datetime.now(UTC):%Y-%m-%d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Load hourly weather into Postgres")
    parser.add_argument("--system-id", help="link this system to this weather source")
    parser.add_argument("--download", nargs=2, metavar=("START", "END"), help="refresh the cached CSV first")
    parser.add_argument("--refresh", action="store_true", help="download from the first inverter reading to today")
    args = parser.parse_args()
    if args.download:
        download_open_meteo(*args.download)
    elif args.refresh:
        download_open_meteo(*refresh_range(args.system_id))
    count = load_weather(args.system_id)
    print(f"{count} horas de clima ({OPEN_METEO_SOURCE_ID}) carregadas")


if __name__ == "__main__":
    main()
