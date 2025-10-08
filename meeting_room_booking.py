"""Utilities for managing meeting room bookings.

This module provides a small in-memory booking manager that can be used to
track meeting rooms, create bookings, check availability, and update or cancel
existing reservations.  The design keeps the public API intentionally
lightweight so that it can be embedded inside other tools such as CLI scripts,
web applications, or notebooks.

Example
-------
>>> from datetime import datetime, timedelta
>>> from meeting_room_booking import BookingManager, MeetingRoom
>>> manager = BookingManager()
>>> manager.add_room(MeetingRoom(name="Atlas", capacity=10, resources={"TV"}))
>>> start = datetime(2024, 1, 1, 9, 0)
>>> end = start + timedelta(hours=1)
>>> booking = manager.book_room(
...     room_name="Atlas",
...     start=start,
...     end=end,
...     title="Product Sync",
...     organizer="alex@example.com",
...     attendees=["sam@example.com"],
... )
>>> manager.find_available_rooms(start, end)
[]
>>> manager.cancel_booking(booking.id)
>>> manager.find_available_rooms(start, end)[0].name
'Atlas'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Set
import uuid


@dataclass(frozen=True)
class MeetingRoom:
    """Metadata describing an individual meeting room."""

    name: str
    capacity: int
    resources: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not normalized_name:
            raise ValueError("Room name must not be empty.")
        if self.capacity <= 0:
            raise ValueError("Room capacity must be a positive integer.")
        normalized_resources = frozenset(sorted(r.strip() for r in self.resources if r.strip()))
        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "resources", normalized_resources)


@dataclass
class Booking:
    """Represents a reservation of a meeting room for a time interval."""

    id: str
    room: MeetingRoom
    start: datetime
    end: datetime
    title: str
    organizer: str
    attendees: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError("Booking start time must be before end time.")
        self.attendees = [attendee.strip() for attendee in self.attendees if attendee.strip()]

    def overlaps(self, other: "Booking") -> bool:
        """Return ``True`` if this booking overlaps with ``other`` for the same room."""

        if self.room.name != other.room.name:
            return False
        return self.start < other.end and other.start < self.end


class BookingManager:
    """Manage meeting rooms and their bookings in memory."""

    def __init__(self) -> None:
        self._rooms: Dict[str, MeetingRoom] = {}
        self._bookings: Dict[str, Booking] = {}
        self._room_index: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    # Room management
    # ------------------------------------------------------------------
    def add_room(self, room: MeetingRoom) -> None:
        """Register a new meeting room.

        Raises
        ------
        ValueError
            If a room with the same name already exists.
        """

        if room.name in self._rooms:
            raise ValueError(f"Room '{room.name}' already exists.")
        self._rooms[room.name] = room
        self._room_index[room.name] = []

    def remove_room(self, room_name: str) -> None:
        """Remove a meeting room and all associated bookings."""

        room_name = room_name.strip()
        if room_name not in self._rooms:
            raise KeyError(f"Room '{room_name}' does not exist.")
        for booking_id in list(self._room_index[room_name]):
            self._bookings.pop(booking_id, None)
        del self._room_index[room_name]
        del self._rooms[room_name]

    def list_rooms(self) -> List[MeetingRoom]:
        """Return all registered rooms sorted by name."""

        return sorted(self._rooms.values(), key=lambda room: room.name)

    def get_room(self, room_name: str) -> MeetingRoom:
        """Retrieve room metadata by name."""

        room_name = room_name.strip()
        try:
            return self._rooms[room_name]
        except KeyError as exc:  # pragma: no cover - defensive programming
            raise KeyError(f"Room '{room_name}' does not exist.") from exc

    # ------------------------------------------------------------------
    # Booking management
    # ------------------------------------------------------------------
    def book_room(
        self,
        *,
        room_name: str,
        start: datetime,
        end: datetime,
        title: str,
        organizer: str,
        attendees: Optional[Iterable[str]] = None,
        notes: Optional[str] = None,
    ) -> Booking:
        """Reserve a room if it is available for the requested interval."""

        room = self.get_room(room_name)
        attendees_list = list(attendees or [])
        new_booking = Booking(
            id=str(uuid.uuid4()),
            room=room,
            start=start,
            end=end,
            title=title.strip() or room.name,
            organizer=organizer.strip(),
            attendees=attendees_list,
            notes=notes.strip() if notes else None,
        )

        self._ensure_availability(new_booking)

        self._bookings[new_booking.id] = new_booking
        self._room_index[room.name].append(new_booking.id)
        self._room_index[room.name].sort(key=lambda booking_id: self._bookings[booking_id].start)
        return new_booking

    def update_booking(
        self,
        booking_id: str,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        room_name: Optional[str] = None,
        title: Optional[str] = None,
        organizer: Optional[str] = None,
        attendees: Optional[Sequence[str]] = None,
        notes: Optional[str] = None,
    ) -> Booking:
        """Update an existing booking and return the modified booking."""

        booking = self._bookings.get(booking_id)
        if booking is None:
            raise KeyError(f"Booking '{booking_id}' does not exist.")

        target_room = self.get_room(room_name) if room_name else booking.room
        new_start = start or booking.start
        new_end = end or booking.end

        updated_booking = Booking(
            id=booking.id,
            room=target_room,
            start=new_start,
            end=new_end,
            title=title.strip() if title else booking.title,
            organizer=organizer.strip() if organizer else booking.organizer,
            attendees=list(attendees) if attendees is not None else list(booking.attendees),
            notes=notes.strip() if notes else booking.notes,
        )

        # Temporarily remove the old booking to allow rescheduling.
        self._remove_booking_from_index(booking)
        try:
            self._ensure_availability(updated_booking)
        except Exception:
            # If the update fails we must re-index the original booking.
            self._room_index[booking.room.name].append(booking.id)
            self._room_index[booking.room.name].sort(key=lambda b_id: self._bookings[b_id].start)
            self._bookings[booking.id] = booking
            raise
        else:
            self._bookings[booking.id] = updated_booking
            self._room_index.setdefault(updated_booking.room.name, []).append(booking.id)
            self._room_index[updated_booking.room.name].sort(
                key=lambda b_id: self._bookings[b_id].start
            )
            return updated_booking

    def cancel_booking(self, booking_id: str) -> Booking:
        """Cancel a booking and return the cancelled booking."""

        booking = self._bookings.pop(booking_id, None)
        if booking is None:
            raise KeyError(f"Booking '{booking_id}' does not exist.")
        self._remove_booking_from_index(booking)
        return booking

    def list_bookings(
        self,
        *,
        room_name: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Booking]:
        """Return bookings filtered by room and/or time range."""

        if room_name:
            booking_ids = self._room_index.get(room_name.strip(), [])
            bookings = [self._bookings[booking_id] for booking_id in booking_ids]
        else:
            bookings = list(self._bookings.values())

        filtered = []
        for booking in bookings:
            if start and booking.end <= start:
                continue
            if end and booking.start >= end:
                continue
            filtered.append(booking)
        return sorted(filtered, key=lambda booking: (booking.room.name, booking.start))

    def find_available_rooms(
        self,
        start: datetime,
        end: datetime,
        *,
        capacity: Optional[int] = None,
        resources: Optional[Iterable[str]] = None,
    ) -> List[MeetingRoom]:
        """Return rooms that are free for the provided time range."""

        if start >= end:
            raise ValueError("Start time must be before end time.")

        required_resources: Set[str] = {resource.strip() for resource in resources or [] if resource.strip()}

        available: List[MeetingRoom] = []
        for room in self.list_rooms():
            if capacity is not None and room.capacity < capacity:
                continue
            if required_resources and not required_resources.issubset(room.resources):
                continue
            probe = Booking(
                id="__probe__",
                room=room,
                start=start,
                end=end,
                title="__probe__",
                organizer="__probe__",
            )
            try:
                self._ensure_availability(probe)
            except ValueError:
                continue
            available.append(room)
        return available

    def get_booking(self, booking_id: str) -> Booking:
        """Retrieve a booking by identifier."""

        booking = self._bookings.get(booking_id)
        if booking is None:
            raise KeyError(f"Booking '{booking_id}' does not exist.")
        return booking

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_availability(self, booking: Booking) -> None:
        """Raise ``ValueError`` if the booking conflicts with existing reservations."""

        for existing_id in self._room_index.get(booking.room.name, []):
            existing = self._bookings[existing_id]
            if booking.id == existing_id:
                continue
            if booking.overlaps(existing):
                raise ValueError(
                    "Room '{room}' is not available between {start:%Y-%m-%d %H:%M} and {end:%Y-%m-%d %H:%M}.".format(
                        room=booking.room.name,
                        start=booking.start,
                        end=booking.end,
                    )
                )

    def _remove_booking_from_index(self, booking: Booking) -> None:
        booking_ids = self._room_index.get(booking.room.name, [])
        try:
            booking_ids.remove(booking.id)
        except ValueError:
            return


__all__ = ["Booking", "BookingManager", "MeetingRoom"]
