from pathlib import Path

import pandas as pd
import requests

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

PLANT_LATITUDE = -8.112
PLANT_LONGITUDE = -35.015
OPEN_METEO_SOURCE_ID = "open-meteo-jaboatao"
OPEN_METEO_CSV = RAW_DIR / "open_meteo_jaboatao_hourly.csv"
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_DAYS = 16
CLIMATE_YEARS = 10
CLIMATE_CSV = RAW_DIR / "open_meteo_jaboatao_hourly_10y.csv"
OPEN_METEO_VARIABLES = {
    "shortwave_radiation": "radiation_wh_m2",
    "temperature_2m": "air_temp_c",
    "relative_humidity_2m": "humidity_pct",
    "precipitation": "precipitation_mm",
    "surface_pressure": "pressure_hpa",
    "wind_speed_10m": "wind_speed_m_s",
}

STATION_ID = "A357"
STATION_PATTERN = f"INMET_NE_PE_{STATION_ID}_PALMARES_*.CSV"

INMET_COLUMNS = {
    "RADIACAO GLOBAL (Kj/m²)": "radiation_kj_m2",
    "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)": "air_temp_c",
    "UMIDADE RELATIVA DO AR, HORARIA (%)": "humidity_pct",
    "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)": "precipitation_mm",
    "PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)": "pressure_hpa",
    "VENTO, VELOCIDADE HORARIA (m/s)": "wind_speed_m_s",
}


def _read_inmet_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", skiprows=8, encoding="latin1", decimal=",", na_values=["-9999"])
    df["measured_at"] = pd.to_datetime(
        df["Data"] + " " + df["Hora UTC"].str[:4], format="%Y/%m/%d %H%M", utc=True
    )
    return df[["measured_at", *INMET_COLUMNS]].rename(columns=INMET_COLUMNS)


def load_inmet_hourly(raw_dir: Path = RAW_DIR, pattern: str = STATION_PATTERN) -> pd.DataFrame:
    paths = sorted(raw_dir.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No INMET CSV matching {pattern} in {raw_dir}")

    df = pd.concat([_read_inmet_csv(p) for p in paths], ignore_index=True)
    df["hour_start"] = df.pop("measured_at") - pd.Timedelta(hours=1)
    df["radiation_wh_m2"] = df.pop("radiation_kj_m2") / 3.6
    return df.drop_duplicates("hour_start").set_index("hour_start").sort_index()


def download_open_meteo(start: str, end: str, path: Path = OPEN_METEO_CSV) -> pd.DataFrame:
    response = requests.get(
        OPEN_METEO_URL,
        params={
            "latitude": PLANT_LATITUDE,
            "longitude": PLANT_LONGITUDE,
            "start_date": start,
            "end_date": end,
            "hourly": ",".join(OPEN_METEO_VARIABLES),
            "timezone": "UTC",
            "wind_speed_unit": "ms",
        },
        timeout=120,
    )
    response.raise_for_status()
    df = pd.DataFrame(response.json()["hourly"]).rename(columns={"time": "measured_at", **OPEN_METEO_VARIABLES})
    df.to_csv(path, index=False)
    return df


def fetch_open_meteo_forecast(days: int = FORECAST_DAYS) -> pd.DataFrame:
    response = requests.get(
        OPEN_METEO_FORECAST_URL,
        params={
            "latitude": PLANT_LATITUDE,
            "longitude": PLANT_LONGITUDE,
            "hourly": ",".join(OPEN_METEO_VARIABLES),
            "timezone": "UTC",
            "wind_speed_unit": "ms",
            "forecast_days": days,
        },
        timeout=60,
    )
    response.raise_for_status()
    df = pd.DataFrame(response.json()["hourly"]).rename(columns=OPEN_METEO_VARIABLES)
    df["hour_start"] = pd.to_datetime(df.pop("time"), utc=True) - pd.Timedelta(hours=1)
    return df.set_index("hour_start").sort_index()


def load_open_meteo_climate(years: int = CLIMATE_YEARS, path: Path = CLIMATE_CSV) -> pd.DataFrame:
    if not path.exists():
        end = pd.Timestamp.now(tz="UTC").normalize().replace(day=1) - pd.Timedelta(days=1)
        start = end - pd.DateOffset(years=years) + pd.Timedelta(days=1)
        download_open_meteo(f"{start:%Y-%m-%d}", f"{end:%Y-%m-%d}", path=path)
    return load_open_meteo_hourly(path)


def load_open_meteo_hourly(path: Path = OPEN_METEO_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["hour_start"] = pd.to_datetime(df.pop("measured_at"), utc=True) - pd.Timedelta(hours=1)
    return df.set_index("hour_start").sort_index()
