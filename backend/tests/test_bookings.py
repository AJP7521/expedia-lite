"""Exercise persistence, validation, and simulated booking lifecycle."""
from fastapi.testclient import TestClient
from app.main import app
from app.controllers.database import connect

client = TestClient(app)


def history():
    response = client.get("/api/bookings")
    assert response.status_code == 200
    return response.json()


def test_booking_lifecycle_and_persistence():
    assert client.get("/api/users").status_code == 404
    assert history() == []
    response = client.post("/api/bookings", json={"trip_id": "T001"})
    assert response.status_code == 201
    booking_id = response.json()["booking_id"]
    row = history()[0]
    assert row["booking_id"] == booking_id
    assert row["stay_price_usd"] == 300
    assert row["status"] == "confirmed"
    response = client.patch(f"/api/bookings/{booking_id}", json={"status": "cancelled"})
    assert response.status_code == 200
    # Every request closes and reopens the database; a fresh client also sees the record.
    with TestClient(app) as restarted:
        rows = restarted.get("/api/bookings").json()
        assert len(rows) == 1
        assert rows[0]["status"] == "cancelled"
    assert client.delete(f"/api/bookings/{booking_id}").status_code == 204
    assert history() == []
    assert client.delete(f"/api/bookings/{booking_id}").status_code == 404


def test_legacy_demo_bookings_are_preserved_but_inaccessible():
    assert history() == []
    assert client.get("/api/bookings?user_id=U001").json() == []
    assert client.patch("/api/bookings/B001", json={"status": "cancelled"}).status_code == 404
    assert client.delete("/api/bookings/B001").status_code == 404
    with connect() as db:
        assert db.execute("SELECT status FROM bookings WHERE booking_id = 'B001'").fetchone()[0] == "confirmed"


def test_invalid_references_and_status():
    assert client.post("/api/bookings", json={"user_id": "missing", "trip_id": "T001"}).status_code == 422
    assert client.post("/api/bookings", json={"trip_id": "missing"}).status_code == 404
    assert client.post("/api/bookings", json={}).status_code == 422
    assert client.patch("/api/bookings/B001", json={"status": "invalid"}).status_code == 422
    assert client.patch("/api/bookings/missing", json={"status": "cancelled"}).status_code == 404
    assert history() == []
