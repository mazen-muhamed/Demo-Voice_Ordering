from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.orders import deps

client = TestClient(app)
P = "/api/v1/sessions"


@pytest.fixture(autouse=True)
def clean():
    deps.store._sessions.clear()


def new():
    return client.post(P, json={}).json()["id"]


def test_full_flow_total_and_confirm():
    sid = new()
    client.post(f"{P}/{sid}/items", json={"name": "كشري", "quantity": 2})
    r = client.post(f"{P}/{sid}/items", json={"name": "ماية"})
    assert r.json()["total"] == 78.0
    r = client.post(f"{P}/{sid}/request-confirmation", json={"ttl_seconds": 30})
    assert r.json()["state"] == "PENDING_CONFIRMATION"
    assert r.json()["confirmation_expires_in_seconds"] == 30
    assert client.post(f"{P}/{sid}/items", json={"item_id": 1}).status_code == 409
    assert client.post(f"{P}/{sid}/confirm").json()["state"] == "CONFIRMED"
    assert client.post(f"{P}/{sid}/cancel").status_code == 409


def test_unknown_item_404_and_empty_confirm_422():
    sid = new()
    assert client.post(f"{P}/{sid}/items", json={"name": "ستيك"}).status_code == 404
    assert client.post(f"{P}/{sid}/request-confirmation").status_code == 422


def test_dtmf_edit_saves_presses():
    sid = new()
    client.post(f"{P}/{sid}/items", json={"item_id": 6, "quantity": 2})
    client.post(f"{P}/{sid}/dtmf", json={"digit": "1"})  # ask confirmation
    client.post(f"{P}/{sid}/dtmf", json={"digit": "2"})  # edit
    for d in ["1", "*", "1", "#"]:  # item 1 -> qty 1
        r = client.post(f"{P}/{sid}/dtmf", json={"digit": d})
    body = r.json()
    assert body["items"][0]["quantity"] == 1
    assert [p["digit"] for p in body["dtmf_history"]] == ["1", "2", "1", "*", "1", "#"]
    r = client.post(f"{P}/{sid}/dtmf", json={"digit": "#"})  # done editing
    assert r.json()["state"] == "PENDING_CONFIRMATION"
    r = client.post(f"{P}/{sid}/dtmf", json={"digit": "1"})
    assert r.json()["state"] == "CONFIRMED"


def test_confirmation_expires():
    sid = new()
    client.post(f"{P}/{sid}/items", json={"item_id": 1})
    client.post(f"{P}/{sid}/request-confirmation", json={"ttl_seconds": 5})
    real = deps.service._now
    deps.service._now = lambda: real() + timedelta(seconds=10)
    try:
        assert client.post(f"{P}/{sid}/confirm").status_code == 410
        assert client.get(f"{P}/{sid}").json()["state"] == "EXPIRED"
    finally:
        deps.service._now = real


def test_websocket_receives_events():
    with client.websocket_connect("/ws/live") as ws:
        assert ws.receive_json()["type"] == "snapshot"
        sid = new()
        assert ws.receive_json()["type"] == "session_created"
        client.post(f"{P}/{sid}/items", json={"item_id": 1})
        assert ws.receive_json()["type"] == "item_added"
