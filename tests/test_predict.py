from __future__ import annotations


def _series(n: int = 80) -> list[float]:
    return [float(i) for i in range(1, n + 1)]


def test_predict_success_charges_and_history(client, register_user):
    headers = register_user("predict@test.com")

    client.post("/balance/top-up", headers=headers, json={"amount": 5})
    balance_before = client.get("/balance", headers=headers).json()["balance"]

    payload = {
        "model": "hf-timeseries",
        "features": {"series": _series(80), "horizon": 5},
    }
    r_predict = client.post("/predict", headers=headers, json=payload)
    assert r_predict.status_code == 200
    task_id = r_predict.json()["task_id"]

    balance_after = client.get("/balance", headers=headers).json()["balance"]
    assert balance_after == balance_before - 1

    r_tx = client.get("/history/transactions", headers=headers)
    assert r_tx.status_code == 200
    txs = r_tx.json()
    assert any(tx["tx_type"] == "CHARGE" for tx in txs)

    r_tasks = client.get("/history/predictions", headers=headers)
    assert r_tasks.status_code == 200
    tasks = r_tasks.json()
    assert any(t["task_id"] == task_id for t in tasks)


def test_predict_insufficient_balance(client, register_user):
    headers = register_user("no-balance@test.com")

    r_predict = client.post(
        "/predict",
        headers=headers,
        json={"model": "hf-timeseries", "features": {"series": _series(50), "horizon": 5}},
    )
    assert r_predict.status_code == 402

    r_balance = client.get("/balance", headers=headers)
    assert r_balance.status_code == 200
    assert r_balance.json()["balance"] == 0

    r_tx = client.get("/history/transactions", headers=headers)
    assert r_tx.status_code == 200
    assert r_tx.json() == []


def test_predict_invalid_payload_no_charge(client, register_user):
    headers = register_user("invalid@test.com")

    client.post("/balance/top-up", headers=headers, json={"amount": 3})
    tx_before = client.get("/history/transactions", headers=headers).json()

    # invalid: horizon <= 0
    r_predict = client.post(
        "/predict",
        headers=headers,
        json={"model": "hf-timeseries", "features": {"series": _series(10), "horizon": 0}},
    )
    assert r_predict.status_code == 422

    tx_after = client.get("/history/transactions", headers=headers).json()
    assert tx_after == tx_before

    balance_after = client.get("/balance", headers=headers).json()["balance"]
    assert balance_after == 3
