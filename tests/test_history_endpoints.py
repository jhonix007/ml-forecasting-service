from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.infrastructure.db.orm_models import MLTaskORM, TransactionORM, UserORM


def test_transactions_history_requires_auth_401(client):
    r = client.get("/history/transactions")

    assert r.status_code == 401


def test_transactions_history_contains_topup_record(client, register_user):
    headers = register_user("history.txs@example.com")

    client.post("/balance/top-up", headers=headers, json={"amount": 7})
    r = client.get("/history/transactions", headers=headers)

    assert r.status_code == 200
    txs = r.json()
    assert len(txs) == 1
    assert txs[0]["tx_type"] == "TOP_UP"
    assert txs[0]["amount"] == 7
    assert txs[0]["comment"] == "api top up"
    assert "created_at" in txs[0]


def test_transactions_history_sorted_by_created_at_desc(client, register_user, session):
    email = "history.txs.sorted@example.com"
    headers = register_user(email)

    user = session.scalar(select(UserORM).where(UserORM.email == email))
    older = TransactionORM(
        user_id=user.id,
        tx_type="TOP_UP",
        amount=1,
        comment="older",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    newer = TransactionORM(
        user_id=user.id,
        tx_type="TOP_UP",
        amount=2,
        comment="newer",
        created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    session.add_all([older, newer])
    session.commit()

    r = client.get("/history/transactions", headers=headers)

    assert r.status_code == 200
    txs = r.json()
    assert [tx["comment"] for tx in txs[:2]] == ["newer", "older"]


def test_predictions_history_requires_auth_401(client):
    r = client.get("/history/predictions")

    assert r.status_code == 401


def test_predictions_history_contains_task_record(client, register_user):
    headers = register_user("history.tasks@example.com")

    client.post("/balance/top-up", headers=headers, json={"amount": 3})
    payload = {"model": "hf-timeseries", "features": {"series": [1.0, 2.0, 3.0], "horizon": 2}}
    r_predict = client.post("/predict", headers=headers, json=payload)

    assert r_predict.status_code == 200
    task_id = r_predict.json()["task_id"]

    r = client.get("/history/predictions", headers=headers)
    assert r.status_code == 200
    tasks = r.json()
    assert any(t["task_id"] == task_id for t in tasks)
    assert all("status" in t and "model" in t and "created_at" in t for t in tasks)


def test_predictions_history_sorted_by_created_at_desc(client, register_user, session):
    email = "history.tasks.sorted@example.com"
    headers = register_user(email)

    user = session.scalar(select(UserORM).where(UserORM.email == email))
    older_task_id = str(uuid4())
    newer_task_id = str(uuid4())
    older = MLTaskORM(
        task_id=older_task_id,
        user_id=user.id,
        model="model-a",
        status="PENDING",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    newer = MLTaskORM(
        task_id=newer_task_id,
        user_id=user.id,
        model="model-b",
        status="PENDING",
        created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    session.add_all([older, newer])
    session.commit()

    r = client.get("/history/predictions", headers=headers)

    assert r.status_code == 200
    tasks = r.json()
    assert [t["task_id"] for t in tasks[:2]] == [newer_task_id, older_task_id]
