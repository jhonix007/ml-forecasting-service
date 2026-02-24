from __future__ import annotations


def test_register_success_returns_token(client):
    payload = {"email": "auth.success@example.com", "password": "test123"}

    r = client.post("/auth/register", json=payload)

    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_email_returns_409(client):
    payload = {"email": "auth.dup@example.com", "password": "test123"}

    r1 = client.post("/auth/register", json=payload)
    r2 = client.post("/auth/register", json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 409


def test_register_invalid_payload_returns_422(client):
    r = client.post("/auth/register", json={"email": "auth.invalid@example.com"})

    assert r.status_code == 422


def test_register_invalid_json_returns_422(client):
    r = client.post(
        "/auth/register",
        data='{"email": "broken"',
        headers={"Content-Type": "application/json"},
    )

    assert r.status_code == 422


def test_login_success_returns_token(client):
    payload = {"email": "auth.login@example.com", "password": "test123"}

    r_register = client.post("/auth/register", json=payload)
    r_login = client.post("/auth/login", json=payload)

    assert r_register.status_code == 200
    assert r_login.status_code == 200
    body = r_login.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    payload = {"email": "auth.wrongpass@example.com", "password": "test123"}

    r_register = client.post("/auth/register", json=payload)
    r_login = client.post("/auth/login", json={"email": payload["email"], "password": "badpass"})

    assert r_register.status_code == 200
    assert r_login.status_code == 401


def test_login_unknown_user_returns_401(client):
    r = client.post("/auth/login", json={"email": "missing@example.com", "password": "test123"})

    assert r.status_code == 401


def test_login_invalid_payload_returns_422(client):
    r = client.post("/auth/login", json={"email": "auth.invalid@example.com"})

    assert r.status_code == 422


def test_login_invalid_json_returns_422(client):
    r = client.post(
        "/auth/login",
        data='{"email": "broken"',
        headers={"Content-Type": "application/json"},
    )

    assert r.status_code == 422
