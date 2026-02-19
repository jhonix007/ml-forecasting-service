from __future__ import annotations


def test_register_and_login(client):
    payload = {"email": "auth@test.com", "password": "test123"}

    r = client.post("/auth/register", json=payload)
    assert r.status_code == 200
    assert "access_token" in r.json()

    r_login = client.post("/auth/login", json=payload)
    assert r_login.status_code == 200
    assert "access_token" in r_login.json()

    r_login_again = client.post("/auth/login", json=payload)
    assert r_login_again.status_code == 200

    r_wrong = client.post("/auth/login", json={"email": payload["email"], "password": "badpass"})
    assert r_wrong.status_code == 401
