import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.hourly_prediction import OBSERVED, HourlyPrediction
from app.models.pv_system import PVSystem
from app.services.refreshing_cache import RefreshingCache

logger = logging.getLogger(__name__)

PLANT_TZ = ZoneInfo("America/Recife")
FEATURE_COLUMNS = [
    "radiation_wh_m2",
    "air_temp_c",
    "hour",
    "day_of_year_sin",
    "day_of_year_cos",
]
CHAMPION_ALIAS = "champion"
MIN_DAYLIGHT_RADIATION_WH_M2 = 2.0


@dataclass(frozen=True)
class Champion:
    version: str
    system_id: str | None
    model_type: str | None
    model: Any


def load_champion_from_mlflow() -> Champion:
    import mlflow.sklearn
    from mlflow import MlflowClient

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    client = MlflowClient()
    version = client.get_model_version_by_alias(settings.registered_model_name, CHAMPION_ALIAS)
    model = mlflow.sklearn.load_model(f"models:/{settings.registered_model_name}/{version.version}")
    return Champion(
        version=str(version.version),
        system_id=version.tags.get("system_id"),
        model_type=version.tags.get("model_type"),
        model=model,
    )


ChampionCache = RefreshingCache[Champion]

champion_cache = ChampionCache(load_champion_from_mlflow)


def model_features(hour_start: datetime, radiation_wh_m2: float, air_temp_c: float) -> pd.DataFrame:
    local = hour_start.astimezone(PLANT_TZ)
    angle = 2 * math.pi * local.timetuple().tm_yday / 365.25
    row = {
        "radiation_wh_m2": radiation_wh_m2,
        "air_temp_c": air_temp_c,
        "hour": local.hour,
        "day_of_year_sin": math.sin(angle),
        "day_of_year_cos": math.cos(angle),
    }
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


def predict_hour(
    db: Session,
    *,
    system: PVSystem,
    hour_start: datetime,
    radiation_wh_m2: float,
    air_temp_c: float | None,
    kind: str = OBSERVED,
    cache: ChampionCache = champion_cache,
) -> HourlyPrediction | None:
    champion = cache.get()
    if champion is None or champion.system_id != str(system.id) or air_temp_c is None:
        return None
    energy_wh = 0.0
    if radiation_wh_m2 > MIN_DAYLIGHT_RADIATION_WH_M2:
        features = model_features(hour_start, radiation_wh_m2, air_temp_c)
        energy_wh = max(0.0, float(champion.model.predict(features)[0]))
    prediction = db.merge(
        HourlyPrediction(
            system_id=system.id,
            hour_start=hour_start,
            kind=kind,
            predicted_energy_wh=energy_wh,
            model_version=champion.version,
        )
    )
    db.commit()
    return prediction
