import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from sungrow_collector.config import Settings
from sungrow_collector.tokens import Tokens, TokenStore

TOKEN_PATH = "/openapi/apiManage/token"
REFRESH_PATH = "/openapi/apiManage/refreshToken"
SUCCESS_CODE = "1"
INVALID_TOKEN_RESULT_CODE = "E00003"
REQUEST_TIMEOUT_SECONDS = 30.0
RETRY_DELAYS_SECONDS = (5.0, 15.0)

logger = logging.getLogger(__name__)


class SungrowError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class ReauthorizationRequired(SungrowError):
    pass


def extract_code(value: str) -> str:
    if value.startswith(("http://", "https://")):
        codes = parse_qs(urlparse(value).query).get("code")
        if not codes:
            raise ValueError("no 'code' parameter found in the URL")
        return codes[0]
    return value


def _is_invalid_token(data: dict[str, Any]) -> bool:
    return data.get("error") == "invalid_token" or data.get("result_code") == INVALID_TOKEN_RESULT_CODE


def _unwrap(data: dict[str, Any]) -> Any:
    if "error" in data:
        raise SungrowError(str(data["error"]), str(data.get("error_description", "")))
    if "result_code" not in data:
        raise SungrowError("bad_response", f"unexpected response fields: {sorted(data)}")
    if str(data.get("result_code")) != SUCCESS_CODE:
        raise SungrowError(str(data.get("result_code")), str(data.get("result_msg", "")))
    return data.get("result_data")


def _unwrap_tokens(data: dict[str, Any]) -> dict[str, Any]:
    if "access_token" in data and "error" not in data:
        return data
    result: dict[str, Any] = _unwrap(data)
    return result


class SungrowClient:
    def __init__(
        self,
        settings: Settings,
        store: TokenStore,
        http: httpx.Client | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._sleep = sleep
        self._store = store
        self._http = http or httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS)
        self._now = now

    def known_ps_ids(self) -> tuple[str, ...]:
        tokens = self._store.load()
        return tokens.ps_ids if tokens else ()

    def exchange_code(self, code: str) -> Tokens:
        data = self._send(
            TOKEN_PATH,
            {
                "appkey": self._settings.appkey,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._settings.redirect_uri,
            },
        )
        result = _unwrap_tokens(data)
        tokens = self._tokens_from(result, ps_ids=tuple(str(ps) for ps in result.get("auth_ps_list", [])))
        self._store.save(tokens)
        return tokens

    def post(self, path: str, body: dict[str, Any]) -> Any:
        tokens = self._valid_tokens()
        payload = {"appkey": self._settings.appkey, **body}
        data = self._send(path, payload, access_token=tokens.access_token)
        if _is_invalid_token(data):
            tokens = self._refresh(tokens)
            data = self._send(path, payload, access_token=tokens.access_token)
        return _unwrap(data)

    def _valid_tokens(self) -> Tokens:
        tokens = self._store.load()
        if tokens is None:
            raise ReauthorizationRequired("no_tokens", "run 'sungrow-collector authorize <code>' first")
        if tokens.is_expiring(self._now()):
            tokens = self._refresh(tokens)
        return tokens

    def _refresh(self, tokens: Tokens) -> Tokens:
        data = self._send(
            REFRESH_PATH,
            {"appkey": self._settings.appkey, "refresh_token": tokens.refresh_token},
        )
        result = _unwrap_tokens(data)
        if "access_token" not in result or str(result.get("code", SUCCESS_CODE)) != SUCCESS_CODE:
            raise ReauthorizationRequired(
                f"refresh_{result.get('code')}",
                "refresh token rejected: the plant owner must authorize again",
            )
        refreshed = self._tokens_from(result, ps_ids=tokens.ps_ids)
        self._store.save(refreshed)
        return refreshed

    def _tokens_from(self, result: dict[str, Any], *, ps_ids: tuple[str, ...]) -> Tokens:
        return Tokens(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_at=self._now() + timedelta(seconds=int(result["expires_in"])),
            ps_ids=ps_ids,
        )

    def _send(self, path: str, payload: dict[str, Any], access_token: str | None = None) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "x-access-key": self._settings.secret_key,
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        response = self._post_with_retry(path, payload, headers, retry=access_token is not None)
        if response.status_code >= 500:
            raise SungrowError(f"http_{response.status_code}", "gateway error")
        data = response.json()
        if not isinstance(data, dict):
            raise SungrowError("bad_response", "response body is not a JSON object")
        return data

    def _post_with_retry(
        self, path: str, payload: dict[str, Any], headers: dict[str, str], *, retry: bool
    ) -> httpx.Response:
        delays = RETRY_DELAYS_SECONDS if retry else ()
        for delay in delays:
            try:
                return self._http.post(f"{self._settings.gateway_url}{path}", json=payload, headers=headers)
            except httpx.TransportError as error:
                logger.warning("%s failed (%s); retrying in %.0f s", path, type(error).__name__, delay)
                self._sleep(delay)
        return self._http.post(f"{self._settings.gateway_url}{path}", json=payload, headers=headers)
