from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import SYSTEM_PAYLOAD


def signup(client, email):
    return client.post("/auth/signup", json={"name": "User", "email": email, "password": "s3cret-pw"})


def test_create_and_list_system(client):
    signup(client, "owner@example.com")

    create_response = client.post("/systems", json=SYSTEM_PAYLOAD)
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["status"] == "awaiting_pairing"
    assert body["device_id"] is None

    list_response = client.get("/systems")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_update_system(client):
    signup(client, "owner@example.com")
    system_id = client.post("/systems", json=SYSTEM_PAYLOAD).json()["id"]

    update_payload = {**SYSTEM_PAYLOAD, "name": "Novo nome", "installed_power_kw": 6.0}
    response = client.patch(f"/systems/{system_id}", json=update_payload)

    assert response.status_code == 200
    assert response.json()["name"] == "Novo nome"
    assert response.json()["installed_power_kw"] == 6.0


def test_delete_system(client):
    signup(client, "owner@example.com")
    system_id = client.post("/systems", json=SYSTEM_PAYLOAD).json()["id"]

    delete_response = client.delete(f"/systems/{system_id}")
    assert delete_response.status_code == 204
    assert client.get("/systems").json() == []


def test_user_cannot_see_or_modify_another_users_system(client):
    signup(client, "owner@example.com")
    system_id = client.post("/systems", json=SYSTEM_PAYLOAD).json()["id"]

    other_client = TestClient(app)
    signup(other_client, "intruder@example.com")

    assert other_client.get(f"/systems/{system_id}").status_code == 404
    assert other_client.patch(f"/systems/{system_id}", json=SYSTEM_PAYLOAD).status_code == 404
    assert other_client.delete(f"/systems/{system_id}").status_code == 404
    assert other_client.get("/systems").json() == []

    assert client.get(f"/systems/{system_id}").status_code == 200


def test_systems_endpoints_require_authentication(client):
    assert client.get("/systems").status_code == 401
    assert client.post("/systems", json=SYSTEM_PAYLOAD).status_code == 401
