import math
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.models.hourly_prediction import HourlyPrediction
from app.models.inverter_reading import InverterReading
from app.models.pv_system import PVSystem
from app.schemas.model_report import (
    FoldScoreOut,
    HourResidualOut,
    ModelReportOut,
    ModelScoreOut,
)
from app.schemas.reading import ReadingIn
from app.services import device_service, inference_service, model_report_service
from app.services.inference_service import (
    Champion,
    ChampionCache,
    model_features,
    predict_hour,
)
from app.services.model_report_service import SystemModelReport
from app.services.prediction_service import real_hourly_energy
from app.services.refreshing_cache import REFRESH_SECONDS, RefreshingCache
from tests.helpers import PLANT_PAYLOAD, signup_and_create_plant

HOUR = datetime(2026, 11, 10, 15, 0, tzinfo=UTC)


class FakeModel:
    def __init__(self, value: float = 20_000.0) -> None:
        self.value = value
        self.inputs = []

    def predict(self, frame):
        self.inputs.append(frame)
        return [self.value]


def fixed_cache(champion: Champion | None) -> ChampionCache:
    return ChampionCache(loader=lambda: champion)


def champion_for(system_id: str, model: FakeModel | None = None) -> Champion:
    return Champion(
        version="6",
        system_id=system_id,
        model_type="random_forest",
        model=model or FakeModel(),
    )


def add_daily_counter(db_session, system_id: str, start: datetime, values_wh: list[float]) -> None:
    for step, value in enumerate(values_wh):
        db_session.add(
            InverterReading(
                system_id=UUID(system_id),
                recorded_at=start + timedelta(minutes=5 * step),
                source="cloud",
                daily_yield_wh=value,
            )
        )
    db_session.commit()


def test_model_features_use_local_hour_and_day_of_year():
    frame = model_features(HOUR, 640.0, 29.1)
    assert list(frame.columns) == inference_service.FEATURE_COLUMNS
    row = frame.iloc[0]
    assert row["hour"] == 12
    assert row["radiation_wh_m2"] == 640.0
    assert row["day_of_year_sin"] == pytest.approx(math.sin(2 * math.pi * 314 / 365.25))


def test_cache_keeps_the_last_champion_when_mlflow_fails():
    now = {"t": 0.0}
    results = iter([champion_for("x"), RuntimeError("mlflow down")])

    def loader():
        result = next(results)
        if isinstance(result, Exception):
            raise result
        return result

    cache = ChampionCache(loader=loader, clock=lambda: now["t"])
    first = cache.get()
    now["t"] = REFRESH_SECONDS + 1
    assert cache.get() is first


def test_predict_hour_only_for_the_system_the_model_was_trained_on(client, db_session):
    mine = signup_and_create_plant(client)
    system = db_session.get(PVSystem, UUID(mine["id"]))

    other = predict_hour(
        db_session,
        system=system,
        hour_start=HOUR,
        radiation_wh_m2=640.0,
        air_temp_c=29.0,
        cache=fixed_cache(champion_for("another-system")),
    )
    assert other is None

    stored = predict_hour(
        db_session,
        system=system,
        hour_start=HOUR,
        radiation_wh_m2=640.0,
        air_temp_c=29.0,
        cache=fixed_cache(champion_for(mine["id"], FakeModel(-5.0))),
    )
    assert stored is not None
    assert stored.predicted_energy_wh == 0.0
    assert stored.model_version == "6"


def test_weather_reading_over_mqtt_triggers_the_prediction(client, db_session, monkeypatch):
    mine = signup_and_create_plant(client)
    model = FakeModel(18_500.0)
    monkeypatch.setattr(
        inference_service,
        "champion_cache",
        fixed_cache(champion_for(mine["id"], model)),
    )
    monkeypatch.setattr(device_service, "predict_hour", _predict_with_patched_cache)
    device_service.ingest_device_reading(db_session, device_id="02534F4C4152", payload=_reading(pairing=True))
    assert client.put(f"/systems/{mine['id']}/device", json={"device_id": "02534F4C4152"}).status_code == 200

    device_service.ingest_device_reading(db_session, device_id="02534F4C4152", payload=_reading())

    prediction = db_session.query(HourlyPrediction).one()
    assert prediction.predicted_energy_wh == 18_500.0
    assert model.inputs[0].iloc[0]["air_temp_c"] == 29.1


def _predict_with_patched_cache(db, **kwargs):
    return predict_hour(db, cache=inference_service.champion_cache, **kwargs)


def _reading(pairing: bool = False) -> ReadingIn:
    return ReadingIn(timestamp=HOUR, irradiance=640.0, ambient_temp_c=29.1, pairing_mode=pairing)


def test_real_energy_comes_from_the_daily_counter(client, db_session):
    mine = signup_and_create_plant(client)
    system = db_session.get(PVSystem, UUID(mine["id"]))
    add_daily_counter(db_session, mine["id"], HOUR, [50_000.0 + 1_000.0 * step for step in range(13)])

    energy = real_hourly_energy(db_session, system=system, hours=[HOUR, HOUR + timedelta(hours=1)])

    assert energy[HOUR] == 12_000.0
    assert energy[HOUR + timedelta(hours=1)] is None


def test_real_energy_starts_from_zero_at_local_midnight(client, db_session):
    mine = signup_and_create_plant(client)
    system = db_session.get(PVSystem, UUID(mine["id"]))
    midnight = datetime(2026, 11, 10, 3, 0, tzinfo=UTC)
    add_daily_counter(
        db_session,
        mine["id"],
        midnight + timedelta(minutes=5),
        [0.0] * 10 + [100.0, 200.0],
    )

    assert real_hourly_energy(db_session, system=system, hours=[midnight])[midnight] == 200.0


def test_predictions_endpoint_pairs_expected_and_real(client, db_session):
    mine = signup_and_create_plant(client)
    db_session.add(
        HourlyPrediction(
            system_id=UUID(mine["id"]),
            hour_start=HOUR,
            kind="observed",
            predicted_energy_wh=13_000.0,
            model_version="6",
        )
    )
    db_session.commit()
    add_daily_counter(db_session, mine["id"], HOUR, [50_000.0 + 1_000.0 * step for step in range(13)])

    rows = client.get(
        f"/systems/{mine['id']}/predictions",
        params={
            "from": (HOUR - timedelta(hours=1)).isoformat(),
            "to": (HOUR + timedelta(hours=2)).isoformat(),
        },
    ).json()

    assert rows == [
        {
            "hour_start": "2026-11-10T15:00:00Z",
            "kind": "observed",
            "predicted_energy_wh": 13_000.0,
            "real_energy_wh": 12_000.0,
            "model_version": "6",
        }
    ]


def test_predictions_require_ownership(client):
    mine = signup_and_create_plant(client, "owner@example.com")
    client.post("/auth/logout")
    signup_and_create_plant(client, "intruder@example.com")
    assert client.get(f"/systems/{mine['id']}/predictions").status_code == 404


def test_predictions_endpoint_separates_expected_from_forecast(client, db_session):
    mine = signup_and_create_plant(client)
    for kind, energy in (("observed", 13_000.0), ("forecast", 15_000.0)):
        db_session.add(
            HourlyPrediction(
                system_id=UUID(mine["id"]),
                hour_start=HOUR,
                kind=kind,
                predicted_energy_wh=energy,
                model_version="6",
            )
        )
        db_session.commit()
    window = {"from": HOUR.isoformat(), "to": (HOUR + timedelta(hours=1)).isoformat()}

    def energies(**params):
        rows = client.get(f"/systems/{mine['id']}/predictions", params=window | params).json()
        return [row["predicted_energy_wh"] for row in rows]

    assert energies() == [13_000.0]
    assert energies(kind="forecast") == [15_000.0]


def _report(system_id: str | None) -> SystemModelReport:
    score = dict.fromkeys(
        [
            "train_rmse_wh",
            "cv_train_rmse_wh",
            "cv_rmse_wh",
            "cv_rmse_std_wh",
            "day_out_rmse_wh",
            "kfold_shuffled_rmse_wh",
            "test_rmse_wh",
            "test_mae_wh",
            "test_r2",
            "test_daily_mape_pct",
        ],
        1.0,
    )
    report = ModelReportOut(
        version="2",
        model_type="random_forest",
        trained_at=HOUR,
        train_period="2025-11-18..2026-08-29",
        test_period="2026-08-30..2026-11-09",
        n_hours=5000,
        performance_ratio=0.71,
        gain_over_baseline_pct=3.0,
        models=[ModelScoreOut(name="random_forest", is_champion=True, is_baseline=False, **score)],
        champion_folds=[FoldScoreOut(fold=1, train_rmse_wh=1.0, validation_rmse_wh=2.0)],
        residuals_by_hour=[HourResidualOut(hour=12, baseline_wh=-100.0, champion_wh=50.0)],
    )
    return SystemModelReport(system_id=system_id, report=report)


def test_model_report_only_for_the_system_the_champion_was_trained_on(client, monkeypatch):
    mine = signup_and_create_plant(client, "owner@example.com")
    other = client.post("/systems", json=PLANT_PAYLOAD).json()
    cache = RefreshingCache(loader=lambda: _report(mine["id"]))
    monkeypatch.setattr(model_report_service, "report_cache", cache)

    response = client.get(f"/systems/{mine['id']}/model")
    assert response.status_code == 200
    assert response.json()["model_type"] == "random_forest"
    assert client.get(f"/systems/{other['id']}/model").status_code == 404


def test_model_report_is_404_while_mlflow_has_no_champion(client, monkeypatch):
    mine = signup_and_create_plant(client)

    def no_champion():
        raise RuntimeError("no champion yet")

    monkeypatch.setattr(model_report_service, "report_cache", RefreshingCache(loader=no_champion))
    assert client.get(f"/systems/{mine['id']}/model").status_code == 404
