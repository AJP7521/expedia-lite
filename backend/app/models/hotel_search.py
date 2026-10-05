"""Provider discoveries are separate from stored, priced Hotel entities."""
from typing import Annotated, Literal

from pydantic import Field

from . import Identifier, Model
from .location import Location

Latitude = Annotated[float, Field(strict=True, ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(strict=True, ge=-180, le=180, allow_inf_nan=False)]


class SearchCenter(Model):
    latitude: Latitude
    longitude: Longitude


class ProviderHotel(SearchCenter):
    provider_place_id: Identifier
    name: str | None = None
    address: str | None = None


class HotelSearchResult(Model):
    location: Location
    search_center: SearchCenter
    radius_meters: Literal[5000] = 5000
    hotels: tuple[ProviderHotel, ...]
