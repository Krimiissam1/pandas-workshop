import unittest
from datetime import datetime, timedelta

from meeting_room_booking import BookingManager, MeetingRoom


class BookingManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = BookingManager()
        self.manager.add_room(MeetingRoom(name="Atlas", capacity=8, resources={"TV", "Whiteboard"}))
        self.manager.add_room(MeetingRoom(name="Zephyr", capacity=4, resources={"Phone"}))

    def test_room_registration(self) -> None:
        rooms = self.manager.list_rooms()
        self.assertEqual([room.name for room in rooms], ["Atlas", "Zephyr"])
        with self.assertRaises(ValueError):
            self.manager.add_room(MeetingRoom(name="Atlas", capacity=10))

    def test_booking_conflict_detection(self) -> None:
        start = datetime(2024, 5, 10, 9, 0)
        end = start + timedelta(hours=2)
        self.manager.book_room(
            room_name="Atlas",
            start=start,
            end=end,
            title="Strategy Meeting",
            organizer="alex@example.com",
        )

        with self.assertRaises(ValueError):
            self.manager.book_room(
                room_name="Atlas",
                start=start + timedelta(minutes=30),
                end=end + timedelta(hours=1),
                title="Sales Review",
                organizer="pat@example.com",
            )

    def test_find_available_rooms_with_filters(self) -> None:
        start = datetime(2024, 5, 10, 13, 0)
        end = start + timedelta(hours=1)
        self.manager.book_room(
            room_name="Atlas",
            start=start,
            end=end,
            title="Design Review",
            organizer="maya@example.com",
        )

        available = self.manager.find_available_rooms(start, end)
        self.assertEqual([room.name for room in available], ["Zephyr"])

        available = self.manager.find_available_rooms(start, end, capacity=6)
        self.assertEqual(available, [])

        available = self.manager.find_available_rooms(start, end, resources={"Phone"})
        self.assertEqual([room.name for room in available], ["Zephyr"])

    def test_update_and_cancel_booking(self) -> None:
        start = datetime(2024, 5, 10, 9, 0)
        end = start + timedelta(hours=1)
        booking = self.manager.book_room(
            room_name="Zephyr",
            start=start,
            end=end,
            title="Daily Standup",
            organizer="alex@example.com",
        )

        new_start = start + timedelta(hours=2)
        new_end = new_start + timedelta(hours=1)
        updated = self.manager.update_booking(booking.id, start=new_start, end=new_end, title="Project Sync")
        self.assertEqual(updated.start, new_start)
        self.assertEqual(updated.end, new_end)
        self.assertEqual(updated.title, "Project Sync")

        retrieved = self.manager.get_booking(booking.id)
        self.assertEqual(retrieved.start, new_start)

        cancelled = self.manager.cancel_booking(booking.id)
        self.assertEqual(cancelled.id, booking.id)
        with self.assertRaises(KeyError):
            self.manager.get_booking(booking.id)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
