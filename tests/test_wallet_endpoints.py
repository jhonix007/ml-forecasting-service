from __future__ import annotations

from sqlalchemy import select

from app.infrastructure.db.orm_models import UserORM, WalletORM


def test_get_balance_requires_auth_401(client):
    r = client.get("/balance")

    assert r.status_code == 401


def test_get_balance_success_returns_zero(client, register_user):
    headers = register_user("wallet.balance@example.com")

    r = client.get("/balance", headers=headers)

    assert r.status_code == 200
    assert r.json()["balance"] == 0


def test_get_balance_wallet_not_found_returns_404(client, register_user, session):
    email = "wallet.missing@example.com"
    headers = register_user(email)

    user = session.scalar(select(UserORM).where(UserORM.email == email))
    wallet = session.get(WalletORM, user.id)
    session.delete(wallet)
    session.commit()

    r = client.get("/balance", headers=headers)

    assert r.status_code == 404


def test_topup_requires_auth_401(client):
    r = client.post("/balance/top-up", json={"amount": 10})

    assert r.status_code == 401


def test_topup_success_increases_balance(client, register_user):
    headers = register_user("wallet.topup@example.com")

    r_topup = client.post("/balance/top-up", headers=headers, json={"amount": 10})
    r_balance = client.get("/balance", headers=headers)

    assert r_topup.status_code == 200
    assert r_topup.json()["balance"] == 10
    assert r_balance.status_code == 200
    assert r_balance.json()["balance"] == 10


def test_topup_invalid_payload_returns_422(client, register_user):
    headers = register_user("wallet.invalidpayload@example.com")

    r = client.post("/balance/top-up", headers=headers, json={"amount": 0})
    r_balance = client.get("/balance", headers=headers)

    assert r.status_code == 422
    assert r_balance.json()["balance"] == 0


def test_topup_invalid_json_returns_422(client, register_user):
    headers = register_user("wallet.invalidjson@example.com")

    r = client.post(
        "/balance/top-up",
        headers={**headers, "Content-Type": "application/json"},
        data='{"amount":',
    )
    r_balance = client.get("/balance", headers=headers)

    assert r.status_code == 422
    assert r_balance.json()["balance"] == 0
