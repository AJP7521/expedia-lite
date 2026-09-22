from fastapi.testclient import TestClient
from app.main import app
from app.controllers.database import connect


def register(client, username="alice"):
    return client.post('/api/accounts', json={"username": username, "password": "classroom"})


def login(client, username="alice"):
    return client.post('/api/login', json={"username": username, "password": "classroom"})


def test_accounts_sessions_and_isolation():
    with TestClient(app) as alice, TestClient(app) as bob:
        assert alice.get('/api/bookings').status_code == 401
        assert alice.get('/api/trips?city=Boston').status_code == 401
        created = register(alice)
        assert created.status_code == 201
        assert 'password' not in created.json()
        assert register(bob, ' ALICE ').status_code == 409
        assert alice.post('/api/login', json={"username": "alice", "password": "bad"}).status_code == 401
        assert login(alice).status_code == 200
        assert alice.get('/api/account').json()['username'] == 'alice'
        booking = alice.post('/api/bookings', json={"trip_id": "T001"}).json()
        assert booking['user_id'] == created.json()['user_id']
        assert alice.get('/api/trips?city=Boston').status_code == 200
        assert register(bob, 'bob').status_code == 201
        assert login(bob, 'bob').status_code == 200
        assert bob.get('/api/bookings').json() == []
        assert bob.patch('/api/bookings/' + booking['booking_id'], json={"status": "cancelled"}).status_code == 404
        assert bob.delete('/api/bookings/' + booking['booking_id']).status_code == 404
        token = alice.cookies.get('expedia_session')
        assert alice.post('/api/logout').status_code == 204
        assert alice.get('/api/account').status_code == 401
        alice.cookies.set('expedia_session', token)
        assert alice.get('/api/account').status_code == 401
        assert login(alice).status_code == 200
        assert len(alice.get('/api/bookings').json()) == 1
        with connect() as db:
            assert db.execute('SELECT user_id FROM searches').fetchone()[0] == created.json()['user_id']
            row = db.execute("SELECT password FROM users WHERE username = 'alice'").fetchone()
            assert row[0] != 'classroom'
            assert db.execute("SELECT user_id FROM bookings WHERE booking_id = 'B001'").fetchone()[0] == 'U001'


def test_old_user_schema_migrates_without_changing_records(monkeypatch, tmp_path):
    import sqlite3
    path = tmp_path / 'legacy.sqlite3'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE users (user_id TEXT PRIMARY KEY, display_name TEXT NOT NULL)')
        db.execute("INSERT INTO users VALUES ('U001', 'Existing name')")
    monkeypatch.setenv('EXPEDIA_DB_PATH', str(path))
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE user_id = 'U001'").fetchone()
        assert row['display_name'] == 'Existing name'
        assert row['username'] is None and row['password'] is None
        assert db.execute("SELECT user_id FROM bookings WHERE booking_id = 'B001'").fetchone()[0] == 'U001'
    with TestClient(app) as client:
        assert register(client).status_code == 201
        assert login(client).status_code == 200
        assert client.get('/api/account').json()['username'] == 'alice'
