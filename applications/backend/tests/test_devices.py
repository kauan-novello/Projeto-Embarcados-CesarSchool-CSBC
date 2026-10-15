from datetime import UTC, datetime, timedelta

from app.models.device import Device
from app.schemas.reading import ReadingIn
from app.services.device_service import ingest_device_reading
from tests.helpers import signup_and_create_system

DEVICE_ID = "A1B2C3D48823"


def publish(db_session, *, pairing_mode=False, device_id=DEVICE_ID):
    payload = ReadingIn.model_validate({"irradiance": 42, "pairing_mode": pairing_mode})
    return ingest_device_reading(db_session, device_id=device_id, payload=payload)


def test_unlinked_device_reading_is_discarded_but_device_is_recorded(client, db_session):
    assert publish(db_session) is None
    device = db_session.get(Device, DEVICE_ID)
    assert device is not None
    assert device.system_id is None


def test_only_devices_in_pairing_mode_are_pairable(client, db_session):
    signup_and_create_system(client)
    publish(db_session, device_id="000000000001")
    publish(db_session, pairing_mode=True)

    pairable = client.get("/devices/pairable").json()
    assert [d["id"] for d in pairable] == [DEVICE_ID]
    assert pairable[0]["label"] == "SolarSense-8823"


def test_device_leaves_pairable_list_after_pairing_window(client, db_session):
    signup_and_create_system(client)
    publish(db_session, pairing_mode=True)
    db_session.get(Device, DEVICE_ID).pairing_seen_at = datetime.now(UTC) - timedelta(minutes=5)
    db_session.commit()

    assert client.get("/devices/pairable").json() == []


def test_linking_routes_readings_to_the_system(client, db_session):
    system = signup_and_create_system(client)
    publish(db_session, pairing_mode=True)

    linked = client.put(f"/systems/{system['id']}/device", json={"device_id": DEVICE_ID})
    assert linked.status_code == 200
    assert linked.json()["device_id"] == DEVICE_ID
    assert client.get("/devices/pairable").json() == []

    assert publish(db_session) is not None
    updated = client.get(f"/systems/{system['id']}").json()
    assert updated["status"] == "online_untrained"
    assert client.get(f"/systems/{system['id']}/readings/latest").json()["irradiance"] == 42


def test_cannot_link_device_outside_pairing_mode(client, db_session):
    system = signup_and_create_system(client)
    publish(db_session)

    response = client.put(f"/systems/{system['id']}/device", json={"device_id": DEVICE_ID})
    assert response.status_code == 404


def test_system_accepts_a_single_device(client, db_session):
    system = signup_and_create_system(client)
    publish(db_session, pairing_mode=True)
    client.put(f"/systems/{system['id']}/device", json={"device_id": DEVICE_ID})
    publish(db_session, pairing_mode=True, device_id="000000000002")

    response = client.put(f"/systems/{system['id']}/device", json={"device_id": "000000000002"})
    assert response.status_code == 409


def test_cannot_link_device_to_another_users_system(client, db_session):
    other_system = signup_and_create_system(client, email="other@example.com")
    client.post("/auth/logout")
    signup_and_create_system(client, email="me@example.com")
    publish(db_session, pairing_mode=True)

    response = client.put(f"/systems/{other_system['id']}/device", json={"device_id": DEVICE_ID})
    assert response.status_code == 404
    assert db_session.get(Device, DEVICE_ID).system_id is None


def test_unlinking_stops_readings_and_keeps_history(client, db_session):
    system = signup_and_create_system(client)
    publish(db_session, pairing_mode=True)
    client.put(f"/systems/{system['id']}/device", json={"device_id": DEVICE_ID})
    publish(db_session)

    unlinked = client.delete(f"/systems/{system['id']}/device")
    assert unlinked.json()["device_id"] is None

    assert publish(db_session) is None
    readings = client.get(f"/systems/{system['id']}/readings").json()
    assert len(readings) == 1
