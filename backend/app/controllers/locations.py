"""Resolve U.S. ZIP codes without persisting provider data."""
import re

import httpx
from pydantic import ValidationError

from .. import config
from ..models.location import Location
from .errors import ConfigurationError, ProviderError


def lookup_zip(postcode: str) -> Location | None:
    """Return a verified location, None if unresolved, or raise ProviderError."""
    if not isinstance(postcode, str) or not re.fullmatch(r"[0-9]{5}", postcode):
        raise ValueError("Enter a five-digit U.S. ZIP code as a string.")
    key = config.GEOAPIFY_API_KEY.strip()
    if not key:
        raise ConfigurationError("Geocoding is not configured.")
    try:
        response = httpx.get(
            "https://api.geoapify.com/v1/geocode/search",
            params={"postcode": postcode, "type": "postcode",
                    "filter": "countrycode:us", "format": "json", "apiKey": key},
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        raise ProviderError("Geocoding provider request failed.") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ProviderError("Geocoding provider returned an invalid response.")
    for result in payload["results"]:
        if not isinstance(result, dict):
            raise ProviderError("Geocoding provider returned an invalid response.")
        if (result.get("postcode") != postcode or result.get("country_code") != "us"
                or result.get("result_type") != "postcode"):
            continue
        locality = next((result[field] for field in ("city", "town", "village", "municipality")
                         if isinstance(result.get(field), str) and result[field].strip()), None)
        try:
            return Location(postcode=postcode, country_code="us", latitude=result.get("lat"),
                            longitude=result.get("lon"), locality=locality)
        except ValidationError:
            continue
    return None
