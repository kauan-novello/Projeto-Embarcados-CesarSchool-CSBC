import contextlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

EXPIRY_MARGIN = timedelta(minutes=10)


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str
    expires_at: datetime
    ps_ids: tuple[str, ...]

    def is_expiring(self, now: datetime) -> bool:
        return now + EXPIRY_MARGIN >= self.expires_at


class TokenStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Tokens | None:
        if not self._path.exists():
            return None
        raw = json.loads(self._path.read_text())
        return Tokens(
            access_token=raw["access_token"],
            refresh_token=raw["refresh_token"],
            expires_at=datetime.fromisoformat(raw["expires_at"]),
            ps_ids=tuple(raw["ps_ids"]),
        )

    def save(self, tokens: Tokens) -> None:
        payload = {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_at": tokens.expires_at.astimezone(UTC).isoformat(),
            "ps_ids": list(tokens.ps_ids),
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(payload, handle)
            os.replace(tmp_path, self._path)
        finally:
            with contextlib.suppress(FileNotFoundError):
                tmp_path.unlink()
