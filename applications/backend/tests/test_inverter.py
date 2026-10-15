from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.models.inverter_reading import InverterReading
from tests.helpers import signup_and_create_plant


def add_inverter_reading(db_session, system_id: str, recorded_at: datetime, power_w: float) -> None:
    db_session.add(
        InverterReading(
            system_id=UUID(system_id),
            recorded_at=recorded_at,
            source="cloud",
            power_w=power_w,
            daily_yield_wh=1000.0,
            total_yield_wh=5_000_000.0,
        )
    )
    db_session.commit()


def test_inverter_latest_is_null_before_any_reading(client):
    system = signup_and_create_plant(client)
    assert client.get(f"/systems/{system['id']}/inverter/latest").json() is None


def test_inverter_latest_returns_most_recent_reading(client, db_session):
    system = signup_and_create_plant(client)
    add_inverter_reading(db_session, system["id"], datetime(2026, 11, 9, 15, 0, tzinfo=UTC), 11000.0)
    add_inverter_reading(db_session, system["id"], datetime(2026, 11, 9, 15, 5, tzinfo=UTC), 11763.0)

    latest = client.get(f"/systems/{system['id']}/inverter/latest").json()
    assert latest["power_w"] == 11763.0
    assert latest["source"] == "cloud"


def test_inverter_latest_requires_ownership(client, db_session):
    system = signup_and_create_plant(client, "owner@example.com")
    add_inverter_reading(db_session, system["id"], datetime(2026, 11, 9, 15, 5, tzinfo=UTC), 11763.0)

    other = TestClient(app)
    other.post(
        "/auth/signup",
        json={
            "name": "Other",
            "email": "intruder@example.com",
            "password": "s3cret-pw",
        },
    )

    assert other.get(f"/systems/{system['id']}/inverter/latest").status_code == 404
