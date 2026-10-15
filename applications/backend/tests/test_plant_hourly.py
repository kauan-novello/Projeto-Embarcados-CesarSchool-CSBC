from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.models.plant_hourly import PlantHourly
from tests.helpers import signup_and_create_plant


def add_hour(db_session, system_id: str, hour: int, humidity_estimated: bool) -> None:
    db_session.add(
        PlantHourly(
            system_id=UUID(system_id),
            hour_start=datetime(2026, 10, 31, hour, tzinfo=UTC),
            energy_wh=15000.0,
            radiation_wh_m2=600.0,
            air_temp_c=29.0,
            humidity_pct=70.0,
            humidity_estimated=humidity_estimated,
            pressure_hpa=1004.0,
            wind_speed_m_s=2.1,
        )
    )
    db_session.commit()


def test_hourly_returns_rows_in_time_order(client, db_session):
    system = signup_and_create_plant(client)
    add_hour(db_session, system["id"], 14, humidity_estimated=True)
    add_hour(db_session, system["id"], 13, humidity_estimated=False)

    response = client.get(f"/systems/{system['id']}/hourly")
    assert response.status_code == 200, response.text
    rows = response.json()
    assert [row["hour_start"][11:13] for row in rows] == ["13", "14"]
    assert rows[1]["humidity_estimated"] is True


def test_hourly_requires_ownership(client, db_session):
    system = signup_and_create_plant(client, "owner@example.com")
    add_hour(db_session, system["id"], 13, humidity_estimated=False)

    other = TestClient(app)
    other.post(
        "/auth/signup",
        json={
            "name": "Other",
            "email": "intruder@example.com",
            "password": "s3cret-pw",
        },
    )

    assert other.get(f"/systems/{system['id']}/hourly").status_code == 404
