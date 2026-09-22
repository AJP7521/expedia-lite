"""Database controller contracts for all entities, references, and transactions."""
import csv
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.controllers.database import DATA_DIR, DatabaseController
from app.controllers.errors import ConflictError, NotFoundError
from app.models import Booking, Hotel, Trip, User


def records():
    return [User(user_id="test-user", display_name="Test user"),
            Hotel(hotel_id="test-hotel", hotel_name="Test hotel", city="Test city",
                  state="PA", nightly_rate_usd=Decimal("123.45")),
            Trip(trip_id="test-trip", hotel_id="test-hotel", trip_name="Test stay",
                 check_in=date(2026, 10, 1), check_out=date(2026, 10, 3)),
            Booking(booking_id="test-booking", user_id="test-user", trip_id="test-trip",
                    booked_on=date(2026, 9, 22), status="confirmed")]


def test_crud_all_models_and_reopen():
    keys = ["user_id", "hotel_id", "trip_id", "booking_id"]
    with DatabaseController() as db:
        for record, key in zip(records(), keys):
            assert db.create(record) == record
            assert db.get(type(record), getattr(record, key)) == record
            assert record in db.list(type(record))
        changes = [{"display_name": "Updated"}, {"nightly_rate_usd": "200.25"},
                   {"trip_name": "Updated stay"}, {"status": "cancelled"}]
        for record, change in zip(records(), changes):
            updated = type(record).model_validate({**record.model_dump(), **change})
            assert db.update(updated) == updated
    with DatabaseController() as db:
        assert db.get(Hotel, "test-hotel").nightly_rate_usd == Decimal("200.25")
        assert db.get(Booking, "test-booking").status == "cancelled"
        for record, key in reversed(list(zip(records(), keys))):
            db.delete(type(record), getattr(record, key))
            with pytest.raises(NotFoundError):
                db.get(type(record), getattr(record, key))
    with DatabaseController() as db:
        with pytest.raises(NotFoundError):
            db.get(Booking, "test-booking")


def test_references_conflicts_and_rollback():
    with DatabaseController() as db:
        with pytest.raises(NotFoundError):
            db.create(records()[2])  # Missing hotel.
        with pytest.raises(NotFoundError):
            db.create(records()[3])  # Missing user and trip.
        for record in records():
            db.create(record)
        with pytest.raises(ConflictError):
            db.create(records()[0])
        for entity, identifier in [(User, "test-user"), (Hotel, "test-hotel"), (Trip, "test-trip")]:
            with pytest.raises(ConflictError):
                db.delete(entity, identifier)
        invalid = Trip.model_validate({**records()[2].model_dump(), "hotel_id": "missing"})
        with pytest.raises(NotFoundError):
            db.update(invalid)
    with pytest.raises(RuntimeError):
        with DatabaseController() as db:
            db.delete(Booking, "test-booking")
            raise RuntimeError("Force transaction rollback")
    with DatabaseController() as db:
        assert db.get(Booking, "test-booking").status == "confirmed"


def test_supplied_csv_models_and_relationships():
    loaded = {}
    for entity, filename, key, count in [(Hotel, "hotels", "hotel_id", 8),
                                         (Trip, "trips", "trip_id", 12),
                                         (User, "users", "user_id", 6),
                                         (Booking, "bookings", "booking_id", 6)]:
        with (DATA_DIR / f"{filename}.csv").open(encoding="utf-8-sig", newline="") as source:
            rows = [entity.model_validate(row) for row in csv.DictReader(source)]
        loaded[entity] = {getattr(row, key): row for row in rows}
        assert len(rows) == len(loaded[entity]) == count
    assert all(row.hotel_id in loaded[Hotel] for row in loaded[Trip].values())
    assert all(row.user_id in loaded[User] and row.trip_id in loaded[Trip]
               for row in loaded[Booking].values())


def test_model_validation():
    with pytest.raises(ValidationError):
        Hotel.model_validate({**records()[1].model_dump(), "nightly_rate_usd": "-1"})
    with pytest.raises(ValidationError):
        Trip.model_validate({**records()[2].model_dump(), "check_out": "2026-09-01"})
    with pytest.raises(ValidationError):
        Booking.model_validate({**records()[3].model_dump(), "status": "unknown"})
