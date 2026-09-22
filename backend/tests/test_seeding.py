"""All supplied records are initial data; SQLite is the source of truth afterward."""
import csv

from fastapi.testclient import TestClient

from app.main import app
from app.models import Booking, Hotel, Trip, User
from app.controllers import database
from app.controllers.database import DatabaseController, connect


def test_all_seed_values_are_preserved():
    with DatabaseController() as db:
        for entity, (table, key) in database.ENTITIES.items():
            with (database.DATA_DIR / f"{table}.csv").open(encoding="utf-8-sig", newline="") as source:
                for row in csv.DictReader(source):
                    record = entity.model_validate(row)
                    assert db.get(entity, getattr(record, key)) == record
        assert len(db.list(Hotel)) == 8
        assert len(db.list(Trip)) == 12
        assert len(db.list(User)) == 7  # Six seeds plus the existing local user.
        assert len(db.list(Booking)) == 6


def test_seed_changes_and_new_bookings_survive_without_csv(monkeypatch, tmp_path):
    with DatabaseController() as db:
        original = db.get(Booking, "B001")
        db.update(Booking(**{**original.model_dump(), "status": "cancelled"}))
        db.delete(Booking, "B002")
    # No CSV file is available after initialization: all operations still work.
    monkeypatch.setattr(database, "DATA_DIR", tmp_path / "no-csvs")
    with TestClient(app) as client:
        identifiers = set()
        for _ in range(8):
            response = client.post("/api/bookings", json={"trip_id": "T001"})
            assert response.status_code == 201
            identifiers.add(response.json()["booking_id"])
        assert len(identifiers) == 8
        assert {row["booking_id"] for row in client.get("/api/bookings").json()} == identifiers
        assert len(client.get("/api/trips?city=Boston").json()) == 4
    with DatabaseController() as db:
        rows = {row.booking_id: row for row in db.list(Booking)}
        assert len(rows) == 13  # Five remaining seeds plus eight new bookings.
        assert rows["B001"].status == "cancelled"
        assert "B002" not in rows
        assert identifiers <= rows.keys()


def test_upgrade_preserves_existing_records_and_runs_once():
    # Reproduce an older database with its original hotels/trips marker only.
    with connect() as db:
        db.execute("DELETE FROM metadata WHERE key = 'users_bookings_seeded_v1'")
        db.execute("DELETE FROM bookings WHERE booking_id != 'B001'")
        db.execute("UPDATE bookings SET status = 'cancelled' WHERE booking_id = 'B001'")
        db.execute("UPDATE users SET display_name = 'Existing name' WHERE user_id = 'U001'")
    with DatabaseController() as db:
        assert len(db.list(Booking)) == 6
        assert db.get(Booking, "B001").status == "cancelled"
        assert db.get(User, "U001").display_name == "Existing name"
        db.delete(Booking, "B002")
    with DatabaseController() as db:
        assert len(db.list(Booking)) == 5
