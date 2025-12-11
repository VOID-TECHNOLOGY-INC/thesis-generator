from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


class SecretNotFoundError(RuntimeError):
    """Raised when a required secret cannot be resolved."""


@dataclass
class SecretManager:
    """Basic secret manager abstraction with optional env fallback."""

    vault: Mapping[str, str] = field(default_factory=dict)
    allow_env_fallback: bool = True

    def get(self, key: str) -> str | None:
        if key in self.vault:
            value = self.vault.get(key)
            return value if value else None
        if self.allow_env_fallback:
            return os.getenv(key) or os.getenv(f"VAULT_{key}")
        return None

    def get_required(self, key: str) -> str:
        value = self.get(key)
        if not value:
            raise SecretNotFoundError(f"Missing required secret: {key}")
        return value


class InMemorySecretManager(SecretManager):
    """Testing-friendly manager that stores secrets in-memory."""

    def __init__(self, initial: Mapping[str, str] | None = None, *, allow_env_fallback: bool = False) -> None:
        super().__init__(vault=dict(initial or {}), allow_env_fallback=allow_env_fallback)


_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+")
_PHONE_PATTERN = re.compile(r"(\+?\d[\d\- ]{7,}\d)")


def mask_pii(text: str) -> str:
    """Redact emails and phone-like patterns from user-supplied text."""

    sanitized = _EMAIL_PATTERN.sub("[REDACTED]", text)
    sanitized = _PHONE_PATTERN.sub("[REDACTED]", sanitized)
    return sanitized


def prune_uploads(upload_dir: Path, *, ttl_days: int = 30) -> list[Path]:
    """Delete uploads older than the TTL to limit retention."""

    removed: list[Path] = []
    if not upload_dir.exists():
        return removed

    cutoff = time.time() - ttl_days * 24 * 60 * 60
    for path in upload_dir.iterdir():
        if not path.is_file():
            continue
        mtime = path.stat().st_mtime
        if mtime < cutoff:
            try:
                path.unlink()
                removed.append(path)
            except OSError:
                continue
    return removed


__all__ = ["InMemorySecretManager", "SecretManager", "SecretNotFoundError", "mask_pii", "prune_uploads"]
