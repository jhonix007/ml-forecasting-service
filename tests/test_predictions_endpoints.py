from __future__ import annotations

from uuid import uuid4


def _series(n: int = 10) -> list[float]:
    return [float(i) for i in range(1, n + 1)]


def test_get_task_requires_auth_401(client):
    r = client.get(f"/predictions/{uuid4()}")

    assert r.status_code == 401


def test_get_task_success_returns_status(client, register_user):
    headers = register_user("predictions.success@example.com")

    client.post("/balance/top-up", headers=headers, json={"amount": 2})
    payload = {"model": "hf-timeseries", "features": {"series": _series(20), "horizon": 2}}
    r_predict = client.post("/predict", headers=headers, json=payload)

    assert r_predict.status_code == 200
    task_id = r_predict.json()["task_id"]

    r = client.get(f"/predictions/{task_id}", headers=headers)

    assert r.status_code == 200
    body = r.json()
    assert body["task_id"] == task_id
    assert body["status"] == "PENDING"
    assert body["model"] == payload["model"]


def test_get_task_not_found_returns_404(client, register_user):
    headers = register_user("predictions.missing@example.com")

    r = client.get(f"/predictions/{uuid4()}", headers=headers)

    assert r.status_code == 404


def test_get_task_invalid_id_returns_422(client, register_user):
    headers = register_user("predictions.invalidid@example.com")

    r = client.get("/predictions/not-a-uuid", headers=headers)

    assert r.status_code == 422


def test_get_task_other_user_returns_404(client, register_user):
    headers_owner = register_user("predictions.owner@example.com")
    headers_other = register_user("predictions.other@example.com")

    client.post("/balance/top-up", headers=headers_owner, json={"amount": 2})
    payload = {"model": "hf-timeseries", "features": {"series": _series(15), "horizon": 2}}
    r_predict = client.post("/predict", headers=headers_owner, json=payload)

    assert r_predict.status_code == 200
    task_id = r_predict.json()["task_id"]

    r = client.get(f"/predictions/{task_id}", headers=headers_other)

    assert r.status_code == 404
