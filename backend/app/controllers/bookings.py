"""Single-user simulated booking rules, independent of HTTP and presentation."""
from datetime import date
from uuid import uuid4

from ..models import Booking, BookingCreate, BookingResult, BookingUpdate, Hotel, Trip
from .database import DatabaseController
from .errors import NotFoundError
from .trips import describe_trip


def _owned_booking(db: DatabaseController, booking_id: str, user_id: str) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking.user_id != user_id:
        raise NotFoundError("Booking not found.")
    return booking


def history(user_id: str) -> list[BookingResult]:
    with DatabaseController() as db:
        bookings = [row for row in db.list(Booking) if row.user_id == user_id]
        bookings.sort(key=lambda row: (-row.booked_on.toordinal(), row.booking_id))
        results = []
        for booking in bookings:
            trip = describe_trip(db, db.get(Trip, booking.trip_id))
            hotel = db.get(Hotel, trip.hotel_id)
            results.append(BookingResult(
                **booking.model_dump(), trip_name=trip.trip_name, check_in=trip.check_in,
                check_out=trip.check_out, hotel_name=trip.hotel_name, city=trip.city,
                nightly_rate_usd=str(hotel.nightly_rate_usd), stay_price_usd=trip.stay_price_usd,
            ))
        return results


def create(body: BookingCreate, user_id: str) -> Booking:
    with DatabaseController() as db:
        return db.create(Booking(booking_id=f"B-{uuid4().hex}", user_id=user_id,
                                 trip_id=body.trip_id, booked_on=date.today(), status="confirmed"))


def cancel(booking_id: str, body: BookingUpdate, user_id: str) -> Booking:
    with DatabaseController() as db:
        booking = _owned_booking(db, booking_id, user_id)
        return db.update(Booking(**{**booking.model_dump(), "status": body.status}))


def delete(booking_id: str, user_id: str) -> None:
    with DatabaseController() as db:
        _owned_booking(db, booking_id, user_id)
        db.delete(Booking, booking_id)
