"""Configuration checks use synthetic values and never expose real credentials."""
import runpy
from pathlib import Path

import dotenv
import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app


@pytest.mark.parametrize("value, expected", [
    (None, "key is not configured"),
    ("", "key is not configured"),
    (" \t\n", "key is not configured"),
    ("synthetic-test-key", "key is configured"),
])
def test_configuration_and_health(value, expected, monkeypatch, tmp_path):
    if value is None:
        monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    else:
        monkeypatch.setenv("GEOAPIFY_API_KEY", value)
    calls = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda **kwargs: calls.append(kwargs))
    helper = Path(config.__file__).resolve()
    monkeypatch.chdir(tmp_path)
    loaded = runpy.run_path(str(helper))
    assert calls == [{"dotenv_path": helper.parents[2] / ".env", "override": False}]
    assert loaded["geoapify_key_status"]() == expected
    monkeypatch.setattr(config, "GEOAPIFY_API_KEY", loaded["GEOAPIFY_API_KEY"])
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "geoapify": expected}
