"""HTTP adapter: validate requests, delegate to controllers, serialize contracts."""
from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from . import config
from .controllers import accounts, bookings, hotel_search, locations, trips
from .controllers.errors import AuthenticationError, ConfigurationError, ConflictError, NotFoundError, ProviderError
from .models.location import Location
from .models.hotel_search import HotelSearchResult
from .models import Booking, BookingCreate, BookingResult, BookingUpdate, TripResult, Account, AccountCreate, Credentials

app = FastAPI(title="Expedia Agent API", version="0.1.0")


@app.exception_handler(NotFoundError)
async def not_found(_request, error):
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(ConflictError)
async def conflict(_request, error):
    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.exception_handler(ValueError)
async def invalid_input(_request, error):
    return JSONResponse(status_code=422, content={"detail": str(error)})


@app.exception_handler(AuthenticationError)
async def unauthorized(_request, error):
    return JSONResponse(status_code=401, content={"detail": str(error)})


def current_user(expedia_session: str | None = Cookie(default=None)) -> Account:
    return accounts.current(expedia_session)


@app.post("/api/accounts", status_code=201, response_model=Account)
def register(body: AccountCreate):
    return accounts.register(body)


@app.post("/api/login", response_model=Account)
def login(body: Credentials, response: Response, expedia_session: str | None = Cookie(default=None)):
    account, token = accounts.login(body, expedia_session)
    response.set_cookie("expedia_session", token, httponly=True, samesite="strict",
                        max_age=accounts.SESSION_SECONDS)
    return account


@app.get("/api/account", response_model=Account)
def account(user: Account = Depends(current_user)):
    return user


@app.post("/api/logout", status_code=204)
def logout(expedia_session: str | None = Cookie(default=None)):
    accounts.logout(expedia_session)
    response = Response(status_code=204)
    response.delete_cookie("expedia_session")
    return response


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "geoapify": config.geoapify_key_status()}


@app.get("/api/demo/zip-location", response_model=Location)
def demo_zip_location():
    return zip_location_response("16802")


@app.get("/api/zip-location", response_model=Location)
def get_zip_location(postcode: str = Query(..., min_length=5, max_length=5, pattern=r"^[0-9]{5}$")):
    return zip_location_response(postcode)


def zip_location_response(postcode: str):
    """Share transport error mapping across the two ZIP endpoints."""
    try:
        location = locations.lookup_zip(postcode)
    except ConfigurationError:
        raise HTTPException(status_code=503, detail="Geocoding is not configured.") from None
    except ProviderError:
        raise HTTPException(status_code=502, detail="Geocoding provider request failed.") from None
    if location is None:
        raise HTTPException(status_code=404, detail=f"ZIP {postcode} could not be resolved.")
    return location


@app.get("/api/trips", response_model=list[TripResult])
def get_trips(city: str = Query(..., min_length=1), user: Account = Depends(current_user)):
    return trips.search_trips(city, user.user_id)


@app.get("/api/bookings", response_model=list[BookingResult])
def get_bookings(user: Account = Depends(current_user)):
    return bookings.history(user.user_id)


@app.post("/api/bookings", status_code=201, response_model=Booking)
def create_booking(body: BookingCreate, user: Account = Depends(current_user)):
    return bookings.create(body, user.user_id)


@app.patch("/api/bookings/{booking_id}", response_model=Booking)
def cancel_booking(booking_id: str, body: BookingUpdate, user: Account = Depends(current_user)):
    return bookings.cancel(booking_id, body, user.user_id)


@app.delete("/api/bookings/{booking_id}", status_code=204)
def delete_booking(booking_id: str, user: Account = Depends(current_user)):
    bookings.delete(booking_id, user.user_id)
    return Response(status_code=204)


@app.get("/api/hotels", response_model=HotelSearchResult)
def get_hotels(postcode: str = Query(..., min_length=5, max_length=5, pattern=r"^[0-9]{5}$"),
               user: Account = Depends(current_user)):
    try:
        return hotel_search.search_hotels(postcode)
    except ConfigurationError:
        raise HTTPException(status_code=503, detail="Hotel search is not configured.") from None
    except ProviderError:
        raise HTTPException(status_code=502, detail="Hotel search could not be completed. Please try again.") from None
