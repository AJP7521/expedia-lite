"""Check the CSV-backed search contract with the supplied sample records."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("city, expected", [
    ("Boston", {"T001", "T002", "T009", "T010"}),
    (" bOsToN ", {"T001", "T002", "T009", "T010"}),
    ("New York", {"T003", "T004", "T011"}),
    ("Philadelphia", {"T005", "T006"}),
    ("Washington", {"T007", "T012"}),
    ("State College", {"T008"}),
    ("Miami", set()),
    ("Bos", set()),
])
def test_city_search(city, expected):
    response = client.get("/api/trips", params={"city": city})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert {trip["trip_id"] for trip in response.json()} == expected
    assert len(response.json()) == len(expected)


def test_join_and_prices_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    trips = client.get("/api/trips", params={"city": "Boston"}).json()
    first = next(trip for trip in trips if trip["trip_id"] == "T001")
    assert first == {
        "trip_id": "T001", "hotel_id": "H001",
        "trip_name": "Boston Harbor Weekend", "hotel_name": "Harbor Lantern Hotel",
        "city": "Boston", "state": "MA",
        "check_in": "2026-09-18", "check_out": "2026-09-20",
        "nights": 2, "nightly_rate_usd": 150, "stay_price_usd": 300,
    }
    second = next(trip for trip in trips if trip["trip_id"] == "T002")
    assert (second["nights"], second["nightly_rate_usd"], second["stay_price_usd"]) == (3, 120, 360)


@pytest.mark.parametrize("params", [{}, {"city": ""}, {"city": "   "}])
def test_city_is_required(params):
    assert client.get("/api/trips", params=params).status_code == 422


def test_health_still_available():
    assert client.get("/api/health").json()["status"] == "ok"
