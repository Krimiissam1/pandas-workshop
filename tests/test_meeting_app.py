from pytest import importorskip
importorskip("flask")
from meeting_app.app import app, rooms


def test_reservation_flow(capsys):
    client = app.test_client()
    payload = {
        "room": "A",
        "start": "2025-01-01T09:00",
        "end": "2025-01-01T10:00",
        "requester": "Alice",
        "email": "alice@example.com",
        "it": ["projector"],
        "beverages": ["tea"],
    }
    # Create reservation
    resp = client.post("/reserve", json=payload)
    assert resp.status_code == 201
    res_id = resp.get_json()["reservation_id"]

    # Head approval
    resp = client.post(f"/approve/head/{res_id}")
    assert resp.get_json()["status"] == "head approved"

    # DAO approval and email confirmation
    resp = client.post(f"/approve/dao/{res_id}")
    assert resp.get_json()["status"] == "reservation confirmed"
    captured = capsys.readouterr().out
    assert "Reservation confirmed for room" in captured

    # Reservation should now be listed
    assert rooms["A"]
