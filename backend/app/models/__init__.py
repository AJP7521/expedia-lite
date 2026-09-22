"""Validated entities and boundary contracts; no persistence or HTTP dependencies."""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Identifier = Annotated[str, Field(min_length=1)]


class Model(BaseModel):
    model_config = {"extra": "forbid", "frozen": True}


class User(Model):
    user_id: Identifier
    display_name: Annotated[str, Field(min_length=1)]
    username: str | None = None
    password: str | None = None
    email: str | None = None


class Hotel(Model):
    hotel_id: Identifier
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]


class Trip(Model):
    trip_id: Identifier
    hotel_id: Identifier
    trip_name: str
    check_in: date
    check_out: date

    @model_validator(mode="after")
    def valid_dates(self):
        if self.check_out <= self.check_in:
            raise ValueError("Check-out must be after check-in.")
        return self


class Booking(Model):
    booking_id: Identifier
    user_id: Identifier
    trip_id: Identifier
    booked_on: date
    status: Literal["confirmed", "cancelled"]


class BookingCreate(Model):
    trip_id: Identifier


class BookingUpdate(Model):
    status: Literal["cancelled"]


class TripResult(Trip):
    hotel_name: str
    city: str
    state: str
    nights: int
    nightly_rate_usd: float
    stay_price_usd: float


class BookingResult(Booking):
    trip_name: str
    check_in: date
    check_out: date
    hotel_name: str
    city: str
    nightly_rate_usd: str
    stay_price_usd: float


class Credentials(Model):
    username: Annotated[str, Field(min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")]
    password: Annotated[str, Field(min_length=1, max_length=256)]

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class AccountCreate(Credentials):
    email: Annotated[str, Field(max_length=254)] | None = None


class Account(Model):
    user_id: str
    username: str
    display_name: str
    email: str | None = None
