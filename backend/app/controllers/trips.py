"""Search and price stays without exposing persistence details to the View."""
from uuid import uuid4

from ..models import Hotel, Trip, TripResult
from .database import DatabaseController


def describe_trip(db: DatabaseController, trip: Trip) -> TripResult:
    hotel = db.get(Hotel, trip.hotel_id)
    nights = (trip.check_out - trip.check_in).days
    return TripResult(**trip.model_dump(), hotel_name=hotel.hotel_name,
                      city=hotel.city, state=hotel.state, nights=nights,
                      nightly_rate_usd=float(hotel.nightly_rate_usd),
                      stay_price_usd=float(hotel.nightly_rate_usd * nights))


def search_trips(city: str, user_id: str) -> list[TripResult]:
    query = city.strip().casefold()
    if not query:
        raise ValueError("Enter a city.")
    with DatabaseController() as db:
        db.record_search(uuid4().hex, user_id, city.strip())
        results = [describe_trip(db, trip) for trip in db.list(Trip)]
        return [trip for trip in results if trip.city.casefold() == query]
