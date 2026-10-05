"""The demo HTTP boundary delegates to a mocked controller only."""
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.controllers import locations
from app.controllers.errors import ConfigurationError, ProviderError
from app.main import app
from app.models.location import Location


def test_demo_success(monkeypatch):
    location = Location(postcode="16802", country_code="us", latitude=40.8,
                        longitude=-77.86, locality="University Park")
    lookup = Mock(return_value=location)
    monkeypatch.setattr(locations, "lookup_zip", lookup)
    response = TestClient(app).get("/api/demo/zip-location")
    lookup.assert_called_once_with("16802")
    assert response.status_code == 200
    assert response.json() == location.model_dump()


@pytest.mark.parametrize("error, status, detail", [
    (None, 404, "ZIP 16802 could not be resolved."),
    (ConfigurationError("secret credential"), 503, "Geocoding is not configured."),
    (ProviderError("secret credential"), 502, "Geocoding provider request failed."),
])
def test_demo_errors(monkeypatch, error, status, detail):
    lookup = Mock(return_value=None, side_effect=error)
    monkeypatch.setattr(locations, "lookup_zip", lookup)
    response = TestClient(app).get("/api/demo/zip-location")
    lookup.assert_called_once_with("16802")
    assert response.status_code == status
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize("postcode", ["16802", "02108", "90210"])
def test_zip_route_preserves_string(monkeypatch, postcode):
    location = Location(postcode=postcode, country_code="us", latitude=40.0, longitude=-77.0)
    lookup = Mock(return_value=location)
    monkeypatch.setattr(locations, "lookup_zip", lookup)
    response = TestClient(app).get("/api/zip-location", params={"postcode": postcode})
    lookup.assert_called_once_with(postcode)
    assert response.status_code == 200
    assert response.json() == location.model_dump()


@pytest.mark.parametrize("postcode", [None, "", "2108", "123456", "abcde", "１２３４５", " 16802", "16802\n", "16802-1234"])
def test_zip_route_rejects_invalid_input(monkeypatch, postcode):
    lookup = Mock()
    monkeypatch.setattr(locations, "lookup_zip", lookup)
    response = TestClient(app).get("/api/zip-location", params={} if postcode is None else {"postcode": postcode})
    assert response.status_code == 422
    lookup.assert_not_called()


@pytest.mark.parametrize("error, status, detail", [
    (None, 404, "ZIP 02108 could not be resolved."),
    (ConfigurationError("secret credential"), 503, "Geocoding is not configured."),
    (ProviderError("secret credential"), 502, "Geocoding provider request failed."),
])
def test_zip_route_errors(monkeypatch, error, status, detail):
    monkeypatch.setattr(locations, "lookup_zip", Mock(return_value=None, side_effect=error))
    response = TestClient(app).get("/api/zip-location", params={"postcode": "02108"})
    assert response.status_code == status
    assert response.json() == {"detail": detail}
