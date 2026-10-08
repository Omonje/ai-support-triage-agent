import pytest

from app.errors import GatewayError
from app.gateways.supabase_kb_repo import SupabaseKBRepo


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        if self._json_data is None:
            raise ValueError("not valid json")
        return self._json_data


class _FakeHttpGet:
    def __init__(self, response=None, exc=None):
        self._response = response or _FakeResponse(json_data=[])
        self._exc = exc
        self.calls = []

    def __call__(self, url, headers=None, params=None):
        self.calls.append({"url": url, "headers": headers, "params": params})
        if self._exc:
            raise self._exc
        return self._response


def test_load_articles_returns_articles_from_the_table():
    rows = [
        {"id": "defect_process", "title": "Defect Process", "content": "Start a claim."},
        {"id": "shipping_policy", "title": "Shipping Policy", "content": "Ships in 3-5 days."},
    ]
    http_get = _FakeHttpGet(response=_FakeResponse(json_data=rows))
    repo = SupabaseKBRepo(url="https://xyz.supabase.co", service_key="key", http_get=http_get)

    articles = repo.load_articles()

    assert len(articles) == 2
    assert articles[0].id == "defect_process"
    assert articles[1].title == "Shipping Policy"


def test_load_articles_sends_the_service_key_in_both_required_headers():
    http_get = _FakeHttpGet(response=_FakeResponse(json_data=[]))
    repo = SupabaseKBRepo(url="https://xyz.supabase.co", service_key="secret-key", http_get=http_get)

    repo.load_articles()

    headers = http_get.calls[0]["headers"]
    assert headers["apikey"] == "secret-key"
    assert headers["Authorization"] == "Bearer secret-key"


def test_load_articles_hits_the_right_table_url():
    http_get = _FakeHttpGet(response=_FakeResponse(json_data=[]))
    repo = SupabaseKBRepo(url="https://xyz.supabase.co/", service_key="key", http_get=http_get)

    repo.load_articles()

    assert http_get.calls[0]["url"] == "https://xyz.supabase.co/rest/v1/kb_articles"


def test_load_articles_raises_gateway_error_on_non_200_status():
    http_get = _FakeHttpGet(response=_FakeResponse(status_code=401, text="invalid key"))
    repo = SupabaseKBRepo(url="https://xyz.supabase.co", service_key="bad-key", http_get=http_get)

    with pytest.raises(GatewayError):
        repo.load_articles()


def test_load_articles_raises_gateway_error_on_request_failure():
    http_get = _FakeHttpGet(exc=RuntimeError("network down"))
    repo = SupabaseKBRepo(url="https://xyz.supabase.co", service_key="key", http_get=http_get)

    with pytest.raises(GatewayError):
        repo.load_articles()


def test_load_articles_raises_gateway_error_on_malformed_json():
    http_get = _FakeHttpGet(response=_FakeResponse(json_data=None))
    repo = SupabaseKBRepo(url="https://xyz.supabase.co", service_key="key", http_get=http_get)

    with pytest.raises(GatewayError):
        repo.load_articles()


def test_load_articles_raises_gateway_error_on_row_missing_a_field():
    http_get = _FakeHttpGet(response=_FakeResponse(json_data=[{"id": "defect_process"}]))
    repo = SupabaseKBRepo(url="https://xyz.supabase.co", service_key="key", http_get=http_get)

    with pytest.raises(GatewayError):
        repo.load_articles()
