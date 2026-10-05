"""Discover hotels around one verified U.S. postcode point, without persistence."""
import httpx
from pydantic import ValidationError

from .. import config
from ..models.hotel_search import HotelSearchResult, ProviderHotel, SearchCenter
from . import locations
from .errors import ConfigurationError, NotFoundError, ProviderError

PAGE_SIZE = 500
MAX_PAGES = 20
RADIUS_METERS = 5000


def search_hotels(postcode: str) -> HotelSearchResult:
    location = locations.lookup_zip(postcode)
    if location is None or location.postcode != postcode or location.country_code != "us":
        raise NotFoundError(f"ZIP {postcode} could not be resolved.")
    center = SearchCenter(latitude=location.latitude, longitude=location.longitude)
    key = config.GEOAPIFY_API_KEY.strip()
    if not key:
        raise ConfigurationError("Hotel search is not configured.")
    hotels = {}
    for page in range(MAX_PAGES):
        try:
            response = httpx.get(
                "https://api.geoapify.com/v2/places",
                params={"categories": "accommodation.hotel",
                        "filter": f"circle:{center.longitude},{center.latitude},{RADIUS_METERS}",
                        "limit": PAGE_SIZE, "offset": page * PAGE_SIZE, "apiKey": key},
                timeout=10.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            raise ProviderError("Hotel provider request failed.") from None
        if (not isinstance(payload, dict) or payload.get("type") != "FeatureCollection"
                or not isinstance(payload.get("features"), list)
                or len(payload["features"]) > PAGE_SIZE):
            raise ProviderError("Hotel provider returned an invalid response.")
        features = payload["features"]
        previous_count = len(hotels)
        for feature in features:
            if (not isinstance(feature, dict) or feature.get("type") != "Feature"
                    or not isinstance(feature.get("properties"), dict)):
                raise ProviderError("Hotel provider returned an invalid response.")
            props = feature["properties"]
            try:
                hotel = ProviderHotel(provider_place_id=props.get("place_id"),
                                      name=props.get("name"), address=props.get("formatted"),
                                      latitude=props.get("lat"), longitude=props.get("lon"))
            except ValidationError:
                raise ProviderError("Hotel provider returned an invalid response.") from None
            hotels.setdefault(hotel.provider_place_id, hotel)
        if len(features) < PAGE_SIZE:
            return HotelSearchResult(location=location, search_center=center,
                                     hotels=tuple(hotels.values()))
        if len(hotels) == previous_count:
            raise ProviderError("Hotel provider pagination did not advance.")
    raise ProviderError("Hotel provider pagination could not be completed.")
