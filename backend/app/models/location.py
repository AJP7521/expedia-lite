"""A geocoded postcode, independent of priced hotel stays."""
from typing import Annotated, Literal

from pydantic import Field

from . import Model


class Location(Model):
    postcode: Annotated[str, Field(pattern=r"^[0-9]{5}$")]
    country_code: Literal["us"]
    latitude: Annotated[float, Field(strict=True, ge=-90, le=90, allow_inf_nan=False)]
    longitude: Annotated[float, Field(strict=True, ge=-180, le=180, allow_inf_nan=False)]
    locality: str | None = None
