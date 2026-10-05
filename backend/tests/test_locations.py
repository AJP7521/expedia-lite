"""Mocked provider checks; never send credentials or make network requests."""
import traceback

import httpx
import pytest

from app import config
from app.controllers import locations
from app.controllers.errors import ProviderError


MATCH = {"postcode": "16802", "country_code": "us", "result_type": "postcode",
         "lat": 40.8, "lon": -77.86, "city": "University Park"}


@pytest.fixture(autouse=True)
def fake_key(monkeypatch):
    monkeypatch.setattr(config, "GEOAPIFY_API_KEY", "synthetic-secret")


def mock_response(monkeypatch, payload, status=200):
    def get(url, *, params, timeout):
        assert url == "https://api.geoapify.com/v1/geocode/search"
        assert params == {"postcode": "16802", "type": "postcode", "filter": "countrycode:us",
                          "format": "json", "apiKey": "synthetic-secret"}
        assert timeout == 10.0
        return httpx.Response(status, json=payload, request=httpx.Request("GET", url, params=params))
    monkeypatch.setattr(locations.httpx, "get", get)


def test_success(monkeypatch):
    mock_response(monkeypatch, {"results": [MATCH]})
    assert locations.lookup_zip("16802").model_dump() == {
        "postcode": "16802", "country_code": "us", "latitude": 40.8,
        "longitude": -77.86, "locality": "University Park"}


def test_optional_locality(monkeypatch):
    mock_response(monkeypatch, {"results": [{**MATCH, "city": None}]})
    assert locations.lookup_zip("16802").locality is None


@pytest.mark.parametrize("changes", [
    {"postcode": "16801"}, {"country_code": "ca"}, {"result_type": "city"},
    {"lat": None}, {"lat": 91}, {"lon": -181}, {"lat": True},
    {"lat": "40.8"},
])
def test_unresolved_mismatch_or_invalid_coordinates(monkeypatch, changes):
    mock_response(monkeypatch, {"results": [{**MATCH, **changes}]})
    assert locations.lookup_zip("16802") is None


def test_empty_results(monkeypatch):
    mock_response(monkeypatch, {"results": []})
    assert locations.lookup_zip("16802") is None


@pytest.mark.parametrize("status", [401, 429, 500])
def test_http_failure_is_sanitized(monkeypatch, status):
    mock_response(monkeypatch, {}, status)
    with pytest.raises(ProviderError) as error:
        locations.lookup_zip("16802")
    rendered = "".join(traceback.format_exception(error.value))
    assert "synthetic-secret" not in rendered
    assert "https://api.geoapify.com" not in rendered


@pytest.mark.parametrize("failure", [httpx.TimeoutException("synthetic-secret"),
                                       httpx.ConnectError("synthetic-secret"),
                                       ValueError("synthetic-secret")])
def test_transport_and_json_failure(monkeypatch, failure):
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(locations.httpx, "get", fail)
    with pytest.raises(ProviderError, match="provider request failed") as error:
        locations.lookup_zip("16802")
    assert "synthetic-secret" not in "".join(traceback.format_exception(error.value))


@pytest.mark.parametrize("payload", [{}, {"results": None}, {"results": [None]}])
def test_malformed_payload(monkeypatch, payload):
    mock_response(monkeypatch, payload)
    with pytest.raises(ProviderError):
        locations.lookup_zip("16802")


@pytest.mark.parametrize("value", [None, 16802, "", "1680", "16802-1234"])
def test_invalid_input_does_not_request(monkeypatch, value):
    monkeypatch.setattr(locations.httpx, "get", lambda *a, **kw: pytest.fail("Unexpected request"))
    with pytest.raises(ValueError):
        locations.lookup_zip(value)


def test_missing_key_does_not_request(monkeypatch):
    monkeypatch.setattr(config, "GEOAPIFY_API_KEY", " \t")
    monkeypatch.setattr(locations.httpx, "get", lambda *a, **kw: pytest.fail("Unexpected request"))
    with pytest.raises(ProviderError, match="not configured"):
        locations.lookup_zip("16802")


@pytest.mark.parametrize("postcode", ["16802", "02108", "90210"])
def test_provider_lookup_preserves_postcode(monkeypatch, postcode):
    def get(url, *, params, timeout):
        assert params["postcode"] == postcode
        assert params["type"] == "postcode"
        assert params["filter"] == "countrycode:us"
        assert timeout == 10.0
        return httpx.Response(200, json={"results": [{**MATCH, "postcode": postcode}]},
                              request=httpx.Request("GET", url))
    monkeypatch.setattr(locations.httpx, "get", get)
    assert locations.lookup_zip(postcode).postcode == postcode
