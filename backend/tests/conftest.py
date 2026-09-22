import pytest


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """Tests never write to the application's live database."""
    monkeypatch.setenv("EXPEDIA_DB_PATH", str(tmp_path / "test.sqlite3"))


@pytest.fixture(autouse=True)
def authenticated_legacy_routes(request):
    """Existing CRUD tests use a local principal; account tests exercise real cookies."""
    from app.main import app, current_user
    from app.models import Account
    if request.node.path.name != "test_accounts.py":
        app.dependency_overrides[current_user] = lambda: Account(
            user_id="local-user", username="local", display_name="My account")
    yield
    app.dependency_overrides.clear()
