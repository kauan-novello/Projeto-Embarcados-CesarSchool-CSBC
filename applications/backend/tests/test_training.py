from uuid import UUID

from app.models.pv_system import PVSystem
from app.schemas.reading import ReadingIn
from app.services.reading_service import ingest_reading
from tests.helpers import signup_and_create_system


def test_start_training_requires_online_untrained_status(client):
    system = signup_and_create_system(client)
    assert system["status"] == "awaiting_pairing"

    response = client.post(f"/systems/{system['id']}/start-training")

    assert response.status_code == 409


def test_start_training_moves_status_and_resets_training_started_at(client, db_session):
    system = signup_and_create_system(client)
    db_system = db_session.get(PVSystem, UUID(system["id"]))
    ingest_reading(
        db_session,
        system=db_system,
        payload=ReadingIn.model_validate(
            {
                "power_w": 800,
                "panel_temp_c": 40,
                "ambient_temp_c": 28,
                "ambient_humidity_pct": 60,
                "irradiance": 70,
            }
        ),
    )

    response = client.post(f"/systems/{system['id']}/start-training")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "training"
    assert body["training_started_at"] != system["training_started_at"]


def test_start_training_requires_ownership(client):
    system = signup_and_create_system(client, "owner@example.com")

    from fastapi.testclient import TestClient

    from app.main import app

    other = TestClient(app)
    other.post(
        "/auth/signup", json={"name": "Other", "email": "intruder@example.com", "password": "s3cret-pw"}
    )

    assert other.post(f"/systems/{system['id']}/start-training").status_code == 404
