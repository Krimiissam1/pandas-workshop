"""Dash application providing a UI for the meeting room booking manager."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

import dash
from dash import Dash, Input, Output, State, dash_table, dcc, html
import plotly.express as px

from meeting_room_booking import BookingManager, MeetingRoom


def _serialize_room(room: MeetingRoom) -> Dict[str, str]:
    return {
        "name": room.name,
        "capacity": room.capacity,
        "resources": ", ".join(sorted(room.resources)) or "None",
    }


def _serialize_booking(manager: BookingManager) -> List[Dict[str, str]]:
    serialized: List[Dict[str, str]] = []
    for booking in manager.list_bookings():
        serialized.append(
            {
                "id": booking.id,
                "room": booking.room.name,
                "start": booking.start.isoformat(timespec="minutes"),
                "end": booking.end.isoformat(timespec="minutes"),
                "title": booking.title,
                "organizer": booking.organizer,
                "attendees": ", ".join(booking.attendees) or "None",
                "notes": booking.notes or "",
            }
        )
    return serialized


def _serialize_availability(manager: BookingManager, start: datetime, end: datetime) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for room in manager.find_available_rooms(start, end):
        rows.append(_serialize_room(room))
    return rows


def _get_datetime_range(start_value: str, end_value: str) -> Tuple[datetime, datetime]:
    try:
        start = datetime.fromisoformat(start_value)
        end = datetime.fromisoformat(end_value)
    except ValueError as exc:
        raise ValueError("Please provide valid start and end datetimes.") from exc
    if start >= end:
        raise ValueError("Start time must be before end time.")
    return start, end


booking_manager = BookingManager()


app: Dash = dash.Dash(__name__)
app.title = "Meeting Room Booking Dashboard"


def _initial_state() -> Dict[str, List[Dict[str, str]]]:
    return {
        "rooms": [_serialize_room(room) for room in booking_manager.list_rooms()],
        "bookings": _serialize_booking(booking_manager),
    }


def layout() -> html.Div:
    return html.Div(
        [
            html.H1("Meeting Room Booking Dashboard"),
            dcc.Store(id="booking-state", data=_initial_state()),
            html.Div(
                [
                    html.H2("Register a New Room"),
                    html.Div(
                        [
                            dcc.Input(id="room-name", type="text", placeholder="Room name"),
                            dcc.Input(
                                id="room-capacity",
                                type="number",
                                placeholder="Capacity",
                                min=1,
                                step=1,
                            ),
                            dcc.Input(
                                id="room-resources",
                                type="text",
                                placeholder="Resources (comma separated)",
                            ),
                            html.Button("Add Room", id="add-room-button", n_clicks=0),
                        ],
                        className="room-form",
                    ),
                    html.Div(id="room-feedback", className="feedback"),
                    dash_table.DataTable(
                        id="rooms-table",
                        columns=[
                            {"name": "Room", "id": "name"},
                            {"name": "Capacity", "id": "capacity"},
                            {"name": "Resources", "id": "resources"},
                        ],
                        data=[],
                        style_table={"maxHeight": "250px", "overflowY": "auto"},
                        style_cell={"textAlign": "left", "padding": "0.5rem"},
                    ),
                ],
                className="rooms-section",
            ),
            html.Hr(),
            html.Div(
                [
                    html.H2("Create a Booking"),
                    html.Div(
                        [
                            dcc.Dropdown(id="booking-room", placeholder="Select a room"),
                            dcc.Input(id="booking-title", type="text", placeholder="Meeting title"),
                            dcc.Input(id="booking-organizer", type="email", placeholder="Organizer email"),
                            dcc.Input(
                                id="booking-attendees",
                                type="text",
                                placeholder="Attendees (comma separated emails)",
                            ),
                            dcc.Input(id="booking-start", type="datetime-local"),
                            dcc.Input(id="booking-end", type="datetime-local"),
                            dcc.Input(id="booking-notes", type="text", placeholder="Notes"),
                            html.Button("Book Room", id="book-room-button", n_clicks=0),
                        ],
                        className="booking-form",
                    ),
                    html.Div(id="booking-feedback", className="feedback"),
                    dash_table.DataTable(
                        id="bookings-table",
                        columns=[
                            {"name": "ID", "id": "id"},
                            {"name": "Room", "id": "room"},
                            {"name": "Start", "id": "start"},
                            {"name": "End", "id": "end"},
                            {"name": "Title", "id": "title"},
                            {"name": "Organizer", "id": "organizer"},
                            {"name": "Attendees", "id": "attendees"},
                            {"name": "Notes", "id": "notes"},
                        ],
                        data=[],
                        style_table={"maxHeight": "300px", "overflowY": "auto"},
                        style_cell={"textAlign": "left", "padding": "0.5rem"},
                    ),
                ],
                className="bookings-section",
            ),
            html.Hr(),
            html.Div(
                [
                    html.H2("Check Availability"),
                    html.Div(
                        [
                            dcc.Input(id="availability-start", type="datetime-local"),
                            dcc.Input(id="availability-end", type="datetime-local"),
                            dcc.Input(
                                id="availability-capacity",
                                type="number",
                                min=1,
                                placeholder="Minimum capacity",
                            ),
                            dcc.Input(
                                id="availability-resources",
                                type="text",
                                placeholder="Required resources (comma separated)",
                            ),
                            html.Button("Find Available Rooms", id="availability-button", n_clicks=0),
                        ],
                        className="availability-form",
                    ),
                    html.Div(id="availability-feedback", className="feedback"),
                    dash_table.DataTable(
                        id="availability-table",
                        columns=[
                            {"name": "Room", "id": "name"},
                            {"name": "Capacity", "id": "capacity"},
                            {"name": "Resources", "id": "resources"},
                        ],
                        data=[],
                        style_table={"maxHeight": "200px", "overflowY": "auto"},
                        style_cell={"textAlign": "left", "padding": "0.5rem"},
                    ),
                ],
                className="availability-section",
            ),
            html.Hr(),
            html.Div(
                [
                    html.H2("Bookings Timeline"),
                    dcc.Graph(id="bookings-timeline"),
                ],
                className="timeline-section",
            ),
        ],
        className="app-container",
    )


app.layout = layout()


@app.callback(
    Output("booking-state", "data"),
    Output("room-feedback", "children"),
    Input("add-room-button", "n_clicks"),
    State("room-name", "value"),
    State("room-capacity", "value"),
    State("room-resources", "value"),
    prevent_initial_call=True,
)
def add_room(
    n_clicks: int,
    name: str,
    capacity_value,
    resources: str,
) -> Tuple[Dict[str, List[Dict[str, str]]], str]:
    try:
        if not name or capacity_value in (None, ""):
            raise ValueError("Room name and capacity are required.")
        resource_items = [res.strip() for res in (resources or "").split(",") if res.strip()]
        booking_manager.add_room(
            MeetingRoom(
                name=name,
                capacity=int(capacity_value),
                resources=frozenset(resource_items),
            )
        )
        message = f"Room '{name}' added successfully."
    except Exception as exc:  # pylint: disable=broad-except
        message = f"Error: {exc}"
    return _initial_state(), message


@app.callback(
    Output("booking-state", "data", allow_duplicate=True),
    Output("booking-feedback", "children"),
    Input("book-room-button", "n_clicks"),
    State("booking-room", "value"),
    State("booking-title", "value"),
    State("booking-organizer", "value"),
    State("booking-attendees", "value"),
    State("booking-start", "value"),
    State("booking-end", "value"),
    State("booking-notes", "value"),
    prevent_initial_call=True,
)
def create_booking(
    n_clicks: int,
    room_name: str,
    title: str,
    organizer: str,
    attendees: str,
    start_value: str,
    end_value: str,
    notes: str,
) -> Tuple[Dict[str, List[Dict[str, str]]], str]:
    try:
        if not room_name:
            raise ValueError("Please select a room to book.")
        if not organizer:
            raise ValueError("Organizer email is required.")
        if not start_value or not end_value:
            raise ValueError("Start and end times are required.")
        start, end = _get_datetime_range(start_value, end_value)
        attendee_list = [item.strip() for item in (attendees or "").split(",") if item.strip()]
        booking_manager.book_room(
            room_name=room_name,
            start=start,
            end=end,
            title=title or room_name,
            organizer=organizer,
            attendees=attendee_list,
            notes=notes,
        )
        message = "Booking created successfully."
    except Exception as exc:  # pylint: disable=broad-except
        message = f"Error: {exc}"
    return _initial_state(), message


@app.callback(
    Output("rooms-table", "data"),
    Output("bookings-table", "data"),
    Output("booking-room", "options"),
    Input("booking-state", "data"),
)
def refresh_tables(state: Dict[str, List[Dict[str, str]]]):
    rooms = state.get("rooms", [])
    bookings = state.get("bookings", [])
    room_options = [{"label": room["name"], "value": room["name"]} for room in rooms]
    return rooms, bookings, room_options


@app.callback(
    Output("bookings-timeline", "figure"),
    Input("booking-state", "data"),
)
def update_timeline(state: Dict[str, List[Dict[str, str]]]):
    bookings = state.get("bookings", [])
    if not bookings:
        return px.scatter(title="No bookings available")
    timeline_rows = []
    for record in bookings:
        try:
            start = datetime.fromisoformat(record["start"])
            end = datetime.fromisoformat(record["end"])
        except ValueError:
            # Fallback to raw strings if conversion fails
            start = record["start"]
            end = record["end"]
        timeline_rows.append({**record, "start": start, "end": end})
    fig = px.timeline(
        timeline_rows,
        x_start="start",
        x_end="end",
        y="room",
        color="organizer",
        hover_data=["title", "attendees", "notes"],
        title="Bookings Timeline",
    )
    fig.update_yaxes(autorange="reversed")
    return fig


@app.callback(
    Output("availability-table", "data"),
    Output("availability-feedback", "children"),
    Input("availability-button", "n_clicks"),
    State("availability-start", "value"),
    State("availability-end", "value"),
    State("availability-capacity", "value"),
    State("availability-resources", "value"),
    prevent_initial_call=True,
)
def find_availability(
    n_clicks: int,
    start_value: str,
    end_value: str,
    capacity_value: str,
    resources_value: str,
):
    try:
        if not start_value or not end_value:
            raise ValueError("Start and end times are required.")
        start, end = _get_datetime_range(start_value, end_value)
        capacity = int(capacity_value) if capacity_value not in (None, "") else None
        resource_items = [item.strip() for item in (resources_value or "").split(",") if item.strip()]
        data = _serialize_availability(booking_manager, start, end)
        if capacity is not None:
            data = [row for row in data if int(row["capacity"]) >= capacity]
        if resource_items:
            requested = set(resource_items)
            filtered = []
            for row in data:
                resources = [] if row["resources"] == "None" else row["resources"].split(", ")
                if requested.issubset(set(resources)):
                    filtered.append(row)
            data = filtered
        message = f"Found {len(data)} available room(s)."
    except Exception as exc:  # pylint: disable=broad-except
        data = []
        message = f"Error: {exc}"
    return data, message


if __name__ == "__main__":
    app.run_server(debug=True)
