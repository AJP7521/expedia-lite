"""Local SQLite storage, seeded exactly once from fictional classroom data."""
import csv
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from datetime import date
from decimal import Decimal
from typing import TypeVar

from ..models import Booking, Hotel, Trip, User
from .errors import ConflictError, NotFoundError

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

DEFAULT_USER_ID = "local-user"


@contextmanager
def connect():
    path = Path(os.environ.get("EXPEDIA_DB_PATH", DATA_DIR / "expedia.sqlite3"))
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY)")
            db.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, display_name TEXT NOT NULL)")
            user_columns = {row["name"] for row in db.execute("PRAGMA table_info(users)")}
            for column in ("username", "password", "email"):
                if column not in user_columns:
                    db.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_username ON users(username COLLATE NOCASE)")
            db.execute("""CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users,
                expires_at INTEGER NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS searches (
                search_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users,
                city TEXT NOT NULL, searched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            db.execute("CREATE TABLE IF NOT EXISTS hotels (hotel_id TEXT PRIMARY KEY, hotel_name TEXT, city TEXT, state TEXT, nightly_rate_usd TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS trips (trip_id TEXT PRIMARY KEY, hotel_id TEXT REFERENCES hotels, trip_name TEXT, check_in TEXT, check_out TEXT)")
            db.execute("""CREATE TABLE IF NOT EXISTS bookings (
                booking_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users,
                trip_id TEXT NOT NULL REFERENCES trips, booked_on TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('confirmed', 'cancelled')))""")
            # Separate markers allow databases from the hotels/trips-only version
            # to receive the remaining seed records without resetting edited data.
            seed_groups = (
                ("seeded", (Hotel, Trip)),
                ("users_bookings_seeded_v1", (User, Booking)),
            )
            for marker, entities in seed_groups:
                if db.execute("SELECT 1 FROM metadata WHERE key = ?", (marker,)).fetchone():
                    continue
                for entity in entities:
                    table, key = ENTITIES[entity]
                    columns = list(entity.model_fields)
                    placeholders = ','.join('?' for _ in columns)
                    with (DATA_DIR / f"{table}.csv").open(encoding="utf-8-sig", newline="") as source:
                        records = [entity.model_validate(row) for row in csv.DictReader(source)]
                    db.executemany(
                        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders}) "
                        f"ON CONFLICT({key}) DO NOTHING",
                        [tuple(_storage(getattr(record, column)) for column in columns)
                         for record in records],
                    )
                db.execute("INSERT INTO metadata VALUES (?)", (marker,))
        with db:
            db.execute("INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)", (DEFAULT_USER_ID, "My account"))
            yield db
    finally:
        db.close()


# SQL identifiers only come from this fixed registry, never caller input.
ENTITIES = {User: ("users", "user_id"), Hotel: ("hotels", "hotel_id"),
            Trip: ("trips", "trip_id"), Booking: ("bookings", "booking_id")}
Entity = TypeVar("Entity", User, Hotel, Trip, Booking)


def _storage(value):
    return str(value) if isinstance(value, (date, Decimal)) else value


class DatabaseController:
    """One connection/transaction per context; returns validated entity objects."""

    def __enter__(self):
        self._connection = connect()
        self._db = self._connection.__enter__()
        return self

    def __exit__(self, *exception):
        return self._connection.__exit__(*exception)

    def get(self, entity: type[Entity], identifier: str) -> Entity:
        table, key = ENTITIES[entity]
        row = self._db.execute(f"SELECT * FROM {table} WHERE {key} = ?", (identifier,)).fetchone()
        if row is None:
            raise NotFoundError(f"{entity.__name__} not found.")
        return entity.model_validate(dict(row))

    def list(self, entity: type[Entity]) -> list[Entity]:
        table, key = ENTITIES[entity]
        return [entity.model_validate(dict(row)) for row in
                self._db.execute(f"SELECT * FROM {table} ORDER BY {key}")]

    def _check_references(self, record):
        if isinstance(record, Trip):
            self.get(Hotel, record.hotel_id)
        elif isinstance(record, Booking):
            self.get(User, record.user_id)
            self.get(Trip, record.trip_id)

    def _write(self, sql, parameters):
        try:
            self._db.execute(sql, parameters)
        except sqlite3.IntegrityError as error:
            raise ConflictError("Duplicate identifier or referenced record cannot be removed.") from error

    def create(self, record: Entity) -> Entity:
        table, _ = ENTITIES[type(record)]
        self._check_references(record)
        values = record.model_dump()
        columns = ','.join(values)
        placeholders = ','.join('?' for _ in values)
        self._write(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                    tuple(_storage(value) for value in values.values()))
        return record

    def update(self, record: Entity) -> Entity:
        table, key = ENTITIES[type(record)]
        self.get(type(record), getattr(record, key))
        self._check_references(record)
        values = record.model_dump(exclude={key})
        assignments = ','.join(f"{column} = ?" for column in values)
        self._write(f"UPDATE {table} SET {assignments} WHERE {key} = ?",
                    (*(_storage(value) for value in values.values()), getattr(record, key)))
        return record

    def delete(self, entity: type[Entity], identifier: str) -> None:
        table, key = ENTITIES[entity]
        self.get(entity, identifier)
        self._write(f"DELETE FROM {table} WHERE {key} = ?", (identifier,))


    def find_user(self, username: str) -> User | None:
        row = self._db.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        return User.model_validate(dict(row)) if row else None

    def save_session(self, token: str, user_id: str, expires_at: int) -> None:
        self.get(User, user_id)
        self._db.execute("INSERT INTO sessions VALUES (?, ?, ?)", (token, user_id, expires_at))

    def session_user(self, token: str, now: int) -> User | None:
        row = self._db.execute("SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?", (token, now)).fetchone()
        return self.get(User, row["user_id"]) if row else None

    def remove_session(self, token: str) -> None:
        self._db.execute("DELETE FROM sessions WHERE token = ?", (token,))

    def record_search(self, search_id: str, user_id: str, city: str) -> None:
        self.get(User, user_id)
        self._db.execute("INSERT INTO searches (search_id, user_id, city) VALUES (?, ?, ?)",
                         (search_id, user_id, city))
