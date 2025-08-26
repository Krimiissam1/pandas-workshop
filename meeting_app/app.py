from __future__ import annotations

"""Simple Flask application to manage meeting room reservations and service requests.

The app stores reservations in memory for demonstration purposes. Clients can
request a meeting room along with optional IT equipment and beverage service.
A two step approval process is required: first the head of sector approves the
request, then the Direction of Administration Operations (DAO) gives the final
approval. After final approval an email confirmation is simulated by printing
the reservation details.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from flask import Flask, jsonify, request

app = Flask(__name__)


@dataclass
class Reservation:
    """Data structure representing a reservation and its state."""

    room: str
    start: datetime
    end: datetime
    requester: str
    email: str
    it_requirements: List[str] = field(default_factory=list)
    beverages: List[str] = field(default_factory=list)
    approved_head: bool = False
    approved_dao: bool = False


# In-memory stores. In a real application this would be a database.
rooms: Dict[str, List[Reservation]] = {"A": [], "B": []}
pending: Dict[int, Reservation] = {}


def is_available(room: str, start: datetime, end: datetime) -> bool:
    """Return True if the room is available for the given time range."""
    for res in rooms.get(room, []):
        if not (end <= res.start or start >= res.end):
            return False
    return True


@app.post("/reserve")
def reserve() -> tuple:
    """Create a reservation request if the room is available."""
    data = request.get_json(force=True)
    room = data["room"]
    start = datetime.fromisoformat(data["start"])
    end = datetime.fromisoformat(data["end"])
    if not is_available(room, start, end):
        return jsonify({"error": "room unavailable"}), 409

    reservation_id = len(pending) + 1
    pending[reservation_id] = Reservation(
        room=room,
        start=start,
        end=end,
        requester=data["requester"],
        email=data["email"],
        it_requirements=data.get("it", []),
        beverages=data.get("beverages", []),
    )
    return jsonify({"reservation_id": reservation_id}), 201


@app.post("/approve/head/<int:res_id>")
def approve_head(res_id: int):
    """Mark a reservation as approved by the head of sector."""
    res = pending.get(res_id)
    if not res:
        return jsonify({"error": "reservation not found"}), 404
    res.approved_head = True
    return jsonify({"status": "head approved"})


@app.post("/approve/dao/<int:res_id>")
def approve_dao(res_id: int):
    """Final approval by the DAO. Confirms reservation and sends email."""
    res = pending.get(res_id)
    if not res or not res.approved_head:
        return jsonify({"error": "not ready for DAO approval"}), 400
    if not is_available(res.room, res.start, res.end):
        return jsonify({"error": "room no longer available"}), 409
    res.approved_dao = True
    rooms[res.room].append(res)
    send_email(res)
    del pending[res_id]
    return jsonify({"status": "reservation confirmed"})


def send_email(reservation: Reservation) -> None:
    """Simulate sending an email confirmation by printing details."""
    message = (
        f"Reservation confirmed for room {reservation.room} from "
        f"{reservation.start:%Y-%m-%d %H:%M} to {reservation.end:%H:%M}. "
        f"IT: {', '.join(reservation.it_requirements) or 'none'}, beverages: "
        f"{', '.join(reservation.beverages) or 'none'}."
    )
    print(f"Sending email to {reservation.email}: {message}")


@app.get("/reservations")
def list_reservations():
    """List all confirmed reservations."""
    output = []
    for room, res_list in rooms.items():
        for res in res_list:
            output.append(
                {
                    "room": room,
                    "start": res.start.isoformat(),
                    "end": res.end.isoformat(),
                    "requester": res.requester,
                }
            )
    return jsonify(output)


if __name__ == "__main__":
    app.run(debug=True)
