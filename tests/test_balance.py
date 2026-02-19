from __future__ import annotations


def test_balance_and_topup(client, register_user):
    headers = register_user("balance@test.com")

    r_balance = client.get("/balance", headers=headers)
    assert r_balance.status_code == 200
    assert r_balance.json()["balance"] == 0

    r_topup = client.post("/balance/top-up", headers=headers, json={"amount": 10})
    assert r_topup.status_code == 200
    assert r_topup.json()["balance"] == 10

    r_balance_after = client.get("/balance", headers=headers)
    assert r_balance_after.status_code == 200
    assert r_balance_after.json()["balance"] == 10
