import json
from datetime import timedelta

import httpx
import pytest

from sungrow_collector.client import ReauthorizationRequired, SungrowError, extract_code
from tests.conftest import FIXED_NOW


def _ok(result_data):
    return httpx.Response(200, json={"result_code": "1", "result_msg": "success", "result_data": result_data})


def test_exchange_code_stores_tokens_and_authorized_plants(make_client, store):
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        seen["headers"] = request.headers
        return _ok(
            {"access_token": "acc", "refresh_token": "ref", "expires_in": 172799, "auth_ps_list": ["700001"]}
        )

    tokens = make_client(handler).exchange_code("CODE1")

    assert seen["body"] == {
        "appkey": "appkey-1",
        "grant_type": "authorization_code",
        "code": "CODE1",
        "redirect_uri": "https://localhost/callback",
    }
    assert seen["headers"]["x-access-key"] == "secret-1"
    assert tokens.expires_at == FIXED_NOW + timedelta(seconds=172799)
    assert store.load() == tokens
    assert tokens.ps_ids == ("700001",)


def test_exchange_code_accepts_tokens_at_top_level(make_client, store):
    def handler(request):
        return httpx.Response(
            200,
            json={
                "access_token": "acc",
                "refresh_token": "ref",
                "expires_in": 172799,
                "auth_ps_list": ["700001"],
            },
        )

    tokens = make_client(handler).exchange_code("CODE1")

    assert store.load() == tokens
    assert tokens.ps_ids == ("700001",)


def test_unknown_response_shape_names_its_fields(make_client):
    def handler(request):
        return httpx.Response(200, json={"foo": 1})

    with pytest.raises(SungrowError, match="foo"):
        make_client(handler).exchange_code("CODE1")


def test_data_call_is_retried_after_a_timeout(make_client, valid_tokens):
    attempts = []

    def handler(request):
        attempts.append(1)
        if len(attempts) < 3:
            raise httpx.ReadTimeout("slow gateway")
        return _ok({"ok": True})

    assert make_client(handler).post("/openapi/x", {}) == {"ok": True}
    assert len(attempts) == 3


def test_code_exchange_is_not_retried(make_client):
    attempts = []

    def handler(request):
        attempts.append(1)
        raise httpx.ReadTimeout("slow gateway")

    with pytest.raises(httpx.ReadTimeout):
        make_client(handler).exchange_code("CODE1")
    assert len(attempts) == 1


def test_post_sends_bearer_and_appkey(make_client, valid_tokens):
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return _ok({"rows": 1})

    result = make_client(handler).post("/x", {"ps_id": "9"})

    assert result == {"rows": 1}
    assert seen["auth"] == "Bearer access-1"
    assert seen["body"] == {"appkey": "appkey-1", "ps_id": "9"}


def test_expiring_token_is_refreshed_before_the_call(make_client, store):
    from sungrow_collector.tokens import Tokens

    store.save(Tokens("old-access", "old-refresh", FIXED_NOW + timedelta(minutes=2), ("700001",)))
    calls = []

    def handler(request):
        calls.append(request.url.path)
        if request.url.path.endswith("/refreshToken"):
            assert json.loads(request.content)["refresh_token"] == "old-refresh"
            return _ok(
                {
                    "code": "1",
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "expires_in": 172799,
                }
            )
        assert request.headers["Authorization"] == "Bearer new-access"
        return _ok("done")

    assert make_client(handler).post("/data", {}) == "done"
    assert calls == ["/openapi/apiManage/refreshToken", "/data"]
    saved = store.load()
    assert saved is not None
    assert saved.refresh_token == "new-refresh"
    assert saved.ps_ids == ("700001",)


def test_invalid_token_response_triggers_one_refresh_and_retry(make_client, valid_tokens):
    attempts = {"data": 0}

    def handler(request):
        if request.url.path.endswith("/refreshToken"):
            return _ok({"code": "1", "access_token": "fresh", "refresh_token": "r2", "expires_in": 100000})
        attempts["data"] += 1
        if request.headers["Authorization"] == "Bearer access-1":
            return httpx.Response(
                200, json={"error": "invalid_token", "error_description": "Invalid access token"}
            )
        return _ok("ok-after-refresh")

    assert make_client(handler).post("/data", {}) == "ok-after-refresh"
    assert attempts["data"] == 2


def test_rejected_refresh_token_requires_reauthorization(make_client, store):
    from sungrow_collector.tokens import Tokens

    store.save(Tokens("a", "r", FIXED_NOW - timedelta(hours=1), ()))

    def handler(request):
        return _ok({"code": "-2"})

    with pytest.raises(ReauthorizationRequired):
        make_client(handler).post("/data", {})


def test_missing_tokens_require_authorization(make_client):
    with pytest.raises(ReauthorizationRequired, match="authorize"):
        make_client(lambda request: _ok(None)).post("/data", {})


def test_business_error_is_raised_with_code(make_client, valid_tokens):
    def handler(request):
        return httpx.Response(
            200, json={"result_code": "E901", "result_msg": "The call frequency is too high"}
        )

    with pytest.raises(SungrowError) as info:
        make_client(handler).post("/data", {})
    assert info.value.code == "E901"


def test_gateway_error_is_a_sungrow_error(make_client, valid_tokens):
    with pytest.raises(SungrowError, match="http_502"):
        make_client(lambda request: httpx.Response(502, text="bad gateway")).post("/data", {})


def test_extract_code_accepts_code_or_full_redirect_url():
    assert extract_code("abc123") == "abc123"
    assert extract_code("https://localhost/callback?code=rFrnww&state=x") == "rFrnww"
    with pytest.raises(ValueError):
        extract_code("https://localhost/callback?error=denied")
