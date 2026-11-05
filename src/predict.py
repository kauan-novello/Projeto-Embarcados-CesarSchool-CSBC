import argparse
import os

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow import MlflowClient
from sqlalchemy import text

from db import add_system_id_argument, get_engine
from features import FEATURE_COLUMNS, LOCAL_TZ, MIN_DAYLIGHT_RADIATION_WH_M2, add_calendar_features
from weather import fetch_open_meteo_forecast, load_open_meteo_climate

REGISTERED_MODEL_NAME = "solarsense-energy-hourly"
CHAMPION_ALIAS = "champion"

OBSERVED_WEATHER_HOURS = text(
    """
    SELECT hour_start, radiation_wh_m2, air_temp_c FROM plant_hourly WHERE system_id = :id
    UNION
    SELECT DISTINCT recorded_at, irradiance, ambient_temp_c FROM sensor_readings
    WHERE system_id = :id AND ambient_temp_c IS NOT NULL
      AND recorded_at > (SELECT coalesce(max(hour_start), 'epoch') FROM plant_hourly WHERE system_id = :id)
    """
)

UPSERT = text(
    """
    INSERT INTO hourly_predictions (system_id, hour_start, kind, predicted_energy_wh, model_version)
    VALUES (:system_id, :hour_start, :kind, :predicted_energy_wh, :model_version)
    ON CONFLICT (system_id, hour_start, kind) DO UPDATE
    SET predicted_energy_wh = EXCLUDED.predicted_energy_wh, model_version = EXCLUDED.model_version,
        created_at = now()
    """
)


UPSERT_TYPICAL = text(
    """
    INSERT INTO monthly_typical_energy (system_id, month, energy_wh, low_wh, high_wh, n_years, model_version)
    VALUES (:system_id, :month, :energy_wh, :low_wh, :high_wh, :n_years, :model_version)
    ON CONFLICT (system_id, month) DO UPDATE
    SET energy_wh = EXCLUDED.energy_wh, low_wh = EXCLUDED.low_wh, high_wh = EXCLUDED.high_wh,
        n_years = EXCLUDED.n_years, model_version = EXCLUDED.model_version, created_at = now()
    """
)
MAX_MISSING_HOURS = 6
MIN_YEARS_TO_TRIM = 5


def load_champion(system_id: str):  # noqa: ANN201
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    version = MlflowClient().get_model_version_by_alias(REGISTERED_MODEL_NAME, CHAMPION_ALIAS)
    if version.tags.get("system_id") != system_id:
        raise SystemExit(f"the champion (v{version.version}) was not trained on system {system_id}")
    return mlflow.sklearn.load_model(f"models:/{REGISTERED_MODEL_NAME}/{version.version}"), str(version.version)


def predict_energy(model, weather: pd.DataFrame) -> pd.Series:  # noqa: ANN001
    df = add_calendar_features(weather.sort_index()).dropna(subset=FEATURE_COLUMNS)
    energy = pd.Series(model.predict(df[FEATURE_COLUMNS]), index=df.index).clip(lower=0)
    return energy.where(df["radiation_wh_m2"] > MIN_DAYLIGHT_RADIATION_WH_M2, 0.0)


def save_predictions(system_id: str, weather: pd.DataFrame, kind: str) -> int:
    model, version = load_champion(system_id)
    energy = predict_energy(model, weather)
    rows = [
        {
            "system_id": system_id,
            "hour_start": hour.to_pydatetime(),
            "kind": kind,
            "predicted_energy_wh": float(value),
            "model_version": version,
        }
        for hour, value in energy.items()
    ]
    if rows:
        with get_engine().begin() as conn:
            conn.execute(UPSERT, rows)
    return len(rows)


def typical_months(energy: pd.Series) -> pd.DataFrame:
    local = energy.tz_convert(LOCAL_TZ).tz_localize(None)
    totals = local.groupby(local.index.to_period("M")).agg(["sum", "count"])
    complete = totals[totals["count"] >= totals.index.days_in_month * 24 - MAX_MISSING_HOURS]["sum"]
    rows = []
    for month, values in complete.groupby(complete.index.month):
        ordered = values.sort_values().to_numpy()
        trim = 1 if len(ordered) >= MIN_YEARS_TO_TRIM else 0
        rows.append(
            {
                "month": int(month),
                "energy_wh": float(ordered.mean()),
                "low_wh": float(ordered[trim]),
                "high_wh": float(ordered[-1 - trim]),
                "n_years": len(ordered),
            }
        )
    return pd.DataFrame(rows)


def save_typical_months(system_id: str) -> int:
    model, version = load_champion(system_id)
    months = typical_months(predict_energy(model, load_open_meteo_climate()))
    rows = [{"system_id": system_id, "model_version": version, **row} for row in months.to_dict("records")]
    if rows:
        with get_engine().begin() as conn:
            conn.execute(UPSERT_TYPICAL, rows)
    return len(rows)


def observed_weather(system_id: str) -> pd.DataFrame:
    hours = pd.read_sql(OBSERVED_WEATHER_HOURS, get_engine(), params={"id": system_id})
    hours["hour_start"] = pd.to_datetime(hours["hour_start"], utc=True)
    return hours.set_index("hour_start")


def forecast_weather() -> pd.DataFrame:
    weather = fetch_open_meteo_forecast()
    now = pd.Timestamp.now(tz="UTC").floor("h")
    return weather[weather.index >= now]


def main() -> None:
    parser = argparse.ArgumentParser(description="Write expected and forecast hourly energy")
    parser.add_argument("mode", choices=["history", "forecast", "typical"])
    add_system_id_argument(parser)
    args = parser.parse_args()
    if args.mode == "typical":
        print(f"{save_typical_months(args.system_id)} meses típicos calculados")
        return
    if args.mode == "history":
        count = save_predictions(args.system_id, observed_weather(args.system_id), "observed")
    else:
        count = save_predictions(args.system_id, forecast_weather(), "forecast")
    print(f"{count} horas previstas ({args.mode})")


if __name__ == "__main__":
    main()
