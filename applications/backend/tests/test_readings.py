from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.models.pv_system import PVSystem
from app.schemas.reading import ReadingIn
from app.services.reading_service import ingest_reading
from tests.helpers import signup_and_create_system


def make_reading(**overrides):
    payload = {
        "power_w": 812.4,
        "panel_temp_c": 41.2,
        "ambient_temp_c": 29.5,
        "ambient_humidity_pct": 61,
        "irradiance": 78,
    }
    payload.update(overrides)
    return ReadingIn.model_validate(payload)


def test_ingest_reading_moves_system_out_of_awaiting_pairing(client, db_session):
    system = signup_and_create_system(client)
    assert system["status"] == "awaiting_pairing"

    db_system = db_session.get(PVSystem, UUID(system["id"]))
    ingest_reading(db_session, system=db_system, payload=make_reading())

    updated = client.get(f"/systems/{system['id']}").json()
    assert updated["status"] == "online_untrained"

    latest = client.get(f"/systems/{system['id']}/readings/latest").json()
    assert latest["power_w"] == 812.4


def test_ingest_reading_above_threshold_creates_alert(client, db_session):
    system = signup_and_create_system(client)
    db_system = db_session.get(PVSystem, UUID(system["id"]))

    ingest_reading(db_session, system=db_system, payload=make_reading(panel_temp_c=70.0))

    alerts = client.get(f"/systems/{system['id']}/alerts").json()
    assert len(alerts) == 1
    assert alerts[0]["panel_temp_c"] == 70.0
    assert alerts[0]["threshold_c"] == 65.0


def test_ingest_reading_below_threshold_creates_no_alert(client, db_session):
    system = signup_and_create_system(client)
    db_system = db_session.get(PVSystem, UUID(system["id"]))

    ingest_reading(db_session, system=db_system, payload=make_reading(panel_temp_c=50.0))

    assert client.get(f"/systems/{system['id']}/alerts").json() == []


def test_readings_latest_is_null_before_any_reading(client):
    system = signup_and_create_system(client)
    assert client.get(f"/systems/{system['id']}/readings/latest").json() is None


def test_readings_and_alerts_require_ownership(client, db_session):
    system = signup_and_create_system(client, "owner@example.com")
    db_system = db_session.get(PVSystem, UUID(system["id"]))
    ingest_reading(db_session, system=db_system, payload=make_reading(panel_temp_c=70.0))

    other = TestClient(app)
    other.post(
        "/auth/signup", json={"name": "Other", "email": "intruder@example.com", "password": "s3cret-pw"}
    )

    assert other.get(f"/systems/{system['id']}/readings").status_code == 404
    assert other.get(f"/systems/{system['id']}/readings/latest").status_code == 404
    assert other.get(f"/systems/{system['id']}/alerts").status_code == 404


def test_ingest_irradiance_only_reading_is_stored_without_alert(client, db_session):
    system = signup_and_create_system(client)
    db_system = db_session.get(PVSystem, UUID(system["id"]))

    ingest_reading(db_session, system=db_system, payload=ReadingIn.model_validate({"irradiance": 42}))

    latest = client.get(f"/systems/{system['id']}/readings/latest").json()
    assert latest["irradiance"] == 42
    assert latest["power_w"] is None
    assert latest["panel_temp_c"] is None
    assert client.get(f"/systems/{system['id']}/alerts").json() == []


def test_ingest_reading_stores_pressure_when_sent(client, db_session):
    system = signup_and_create_system(client)
    db_system = db_session.get(PVSystem, UUID(system["id"]))

    payload = ReadingIn.model_validate({"irradiance": 60, "ambient_temp_c": 28.4, "pressure_hpa": 1012.3})
    ingest_reading(db_session, system=db_system, payload=payload)

    latest = client.get(f"/systems/{system['id']}/readings/latest").json()
    assert latest["pressure_hpa"] == 1012.3
    assert latest["ambient_temp_c"] == 28.4
    assert latest["ambient_humidity_pct"] is None


def test_ingest_reading_stores_particulate_when_sent(client, db_session):
    system = signup_and_create_system(client)
    db_system = db_session.get(PVSystem, UUID(system["id"]))

    payload = ReadingIn.model_validate({"irradiance": 60, "particulate_pct": 23.8})
    ingest_reading(db_session, system=db_system, payload=payload)

    latest = client.get(f"/systems/{system['id']}/readings/latest").json()
    assert latest["particulate_pct"] == 23.8
    assert latest["pressure_hpa"] is None
