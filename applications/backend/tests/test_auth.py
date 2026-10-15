def signup(client, email="jane@example.com", password="s3cret-pw"):
    return client.post("/auth/signup", json={"name": "Jane Doe", "email": email, "password": password})


def test_signup_sets_session_cookie_and_returns_user(client):
    response = signup(client)

    assert response.status_code == 201
    assert response.json()["email"] == "jane@example.com"
    assert "solarsense_session" in response.cookies


def test_signup_rejects_duplicate_email(client):
    signup(client)
    response = signup(client)

    assert response.status_code == 400


def test_login_with_correct_credentials(client):
    signup(client, password="s3cret-pw")

    response = client.post("/auth/login", json={"email": "jane@example.com", "password": "s3cret-pw"})

    assert response.status_code == 200
    assert "solarsense_session" in response.cookies


def test_login_with_wrong_password_is_rejected(client):
    signup(client, password="s3cret-pw")

    response = client.post("/auth/login", json={"email": "jane@example.com", "password": "wrong-pw"})

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user_when_logged_in(client):
    signup(client)

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "jane@example.com"


def test_logout_clears_session(client):
    signup(client)
    assert client.get("/auth/me").status_code == 200

    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 204

    assert client.get("/auth/me").status_code == 401
