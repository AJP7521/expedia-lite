"""Exercise resolution and every Places page without network or live storage."""
import traceback

import httpx
import pytest
from fastapi.testclient import TestClient

from app import config
from app.controllers import hotel_search
from app.main import app, current_user

MATCH = {"postcode": "02108", "country_code": "us", "result_type": "postcode",
         "lat": 42.36, "lon": -71.06, "city": "Boston"}


def feature(id="provider-1", **changes):
    return {"type": "Feature", "properties": {"place_id": id, "name": "Test Hotel",
            "formatted": "Boston", "lat": 42.361, "lon": -71.061, **changes}}


def install(monkeypatch, pages=(), resolved=None):
    monkeypatch.setattr(config, "GEOAPIFY_API_KEY", "synthetic-secret")
    calls = []
    def get(url, *, params, timeout):
        assert timeout == 10.0
        if url.endswith('/geocode/search'):
            assert params['postcode'] == '02108'
            assert params['filter'] == 'countrycode:us'
            payload = {"results": [MATCH]} if resolved is None else resolved
        else:
            assert url == 'https://api.geoapify.com/v2/places'
            assert params == {"categories": "accommodation.hotel", "filter": "circle:-71.06,42.36,5000",
                              "limit": hotel_search.PAGE_SIZE, "offset": len(calls) * hotel_search.PAGE_SIZE,
                              "apiKey": "synthetic-secret"}
            payload = pages[len(calls)]
            calls.append(params)
            if isinstance(payload, Exception):
                raise payload
            if isinstance(payload, int):
                return httpx.Response(payload, request=httpx.Request('GET', url))
        return httpx.Response(200, json=payload, request=httpx.Request('GET', url))
    monkeypatch.setattr(hotel_search.httpx, 'get', get)
    return calls


def page(*features):
    return {"type": "FeatureCollection", "features": list(features)}


def search():
    return TestClient(app).get('/api/hotels', params={'postcode': '02108'})


def test_pages_center_deduplication_and_response(monkeypatch):
    monkeypatch.setattr(hotel_search, 'PAGE_SIZE', 2)
    calls = install(monkeypatch, [page(feature('a'), feature('b')), page(feature('b'), feature('c')), page()])
    response = search()
    assert response.status_code == 200
    data = response.json()
    assert data['location'] == {"postcode": "02108", "country_code": "us", "latitude": 42.36,
                                "longitude": -71.06, "locality": "Boston"}
    assert data['search_center'] == {'latitude': 42.36, 'longitude': -71.06}
    assert data['radius_meters'] == 5000
    assert [h['provider_place_id'] for h in data['hotels']] == ['a', 'b', 'c']
    assert all('hotel_id' not in h and 'nightly_rate_usd' not in h for h in data['hotels'])
    assert len(calls) == 3


def test_empty_hotels(monkeypatch):
    install(monkeypatch, [page()])
    assert search().json()['hotels'] == []


@pytest.mark.parametrize('changes', [ {'postcode': '90210'}, {'country_code': 'ca'},
    {'result_type': 'city'}, {'lat': None}, {'lat': 91}, {'lon': -181}, {'lat': True}, {'lon': '42'}])
def test_failed_resolution_never_searches_places(monkeypatch, changes):
    calls = install(monkeypatch, resolved={'results': [{**MATCH, **changes}]})
    assert search().status_code == 404
    assert calls == []


def test_unresolved(monkeypatch):
    calls = install(monkeypatch, resolved={'results': []})
    assert search().status_code == 404
    assert calls == []


@pytest.mark.parametrize('postcode', [None, '', '1234', '02108-1234', ' 02108', 'ABCDE', '１２３４５', '02108\n'])
def test_invalid_never_calls_provider(monkeypatch, postcode):
    monkeypatch.setattr(hotel_search.httpx, 'get', lambda *a, **kw: pytest.fail('Provider called'))
    response = TestClient(app).get('/api/hotels', params={} if postcode is None else {'postcode': postcode})
    assert response.status_code == 422


@pytest.mark.parametrize('payload', [401, 429, 500, httpx.TimeoutException('synthetic-secret'),
    ValueError('synthetic-secret'), {}, {'type': 'FeatureCollection', 'features': None},
    page(None), page(feature(lat=91)), page(feature(place_id=None))])
def test_provider_errors_never_return_partial_results(monkeypatch, payload):
    monkeypatch.setattr(hotel_search, 'PAGE_SIZE', 1)
    install(monkeypatch, [page(feature()), payload])
    response = search()
    assert response.status_code == 502
    assert response.json() == {'detail': 'Hotel search could not be completed. Please try again.'}


def test_repeated_page_fails(monkeypatch):
    monkeypatch.setattr(hotel_search, 'PAGE_SIZE', 1)
    install(monkeypatch, [page(feature()), page(feature())])
    assert search().status_code == 502


def test_page_limit_fails_explicitly(monkeypatch):
    monkeypatch.setattr(hotel_search, 'PAGE_SIZE', 1)
    monkeypatch.setattr(hotel_search, 'MAX_PAGES', 1)
    install(monkeypatch, [page(feature())])
    assert search().status_code == 502


def test_missing_configuration(monkeypatch):
    monkeypatch.setattr(config, 'GEOAPIFY_API_KEY', '')
    monkeypatch.setattr(hotel_search.httpx, 'get', lambda *a, **kw: pytest.fail('Provider called'))
    assert search().status_code == 503


def test_geocode_failure_does_not_search_hotels(monkeypatch):
    calls = install(monkeypatch, resolved={})
    assert search().status_code == 502
    assert calls == []


def test_requires_session(monkeypatch):
    app.dependency_overrides.pop(current_user, None)
    monkeypatch.setattr(hotel_search.httpx, 'get', lambda *a, **kw: pytest.fail('Provider called'))
    assert search().status_code == 401


def test_exception_does_not_expose_credentials(monkeypatch):
    install(monkeypatch, [httpx.ConnectError('synthetic-secret')])
    with pytest.raises(hotel_search.ProviderError) as error:
        hotel_search.search_hotels('02108')
    assert 'synthetic-secret' not in ''.join(traceback.format_exception(error.value))
