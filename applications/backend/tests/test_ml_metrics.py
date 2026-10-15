from uuid import UUID

from app.models.ml_prediction import MLPrediction
from tests.helpers import signup_and_create_system


def test_ml_metrics_is_null_before_ml_writes_anything(client):
    system = signup_and_create_system(client)
    assert client.get(f"/systems/{system['id']}/ml-metrics").json() is None


def test_ml_metrics_returns_latest_prediction(client, db_session):
    system = signup_and_create_system(client)

    db_session.add(
        MLPrediction(
            system_id=UUID(system["id"]),
            predicted_efficiency_pct=17.8,
            predicted_generation_kwh_next_day=21.4,
            model_version="rf-v1",
        )
    )
    db_session.commit()

    response = client.get(f"/systems/{system['id']}/ml-metrics").json()
    assert response["model_version"] == "rf-v1"
    assert response["predicted_efficiency_pct"] == 17.8
