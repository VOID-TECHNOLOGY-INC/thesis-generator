from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from thesis_generator.security import InMemorySecretManager, SecretManager

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """Application configuration resolved through a secret manager."""

    model_config = ConfigDict(extra="ignore")

    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    scite_api_key: str = Field(alias="SCITE_API_KEY")
    openalex_mailto: str | None = Field(default=None, alias="OPENALEX_MAILTO")
    e2b_api_key: str | None = Field(default=None, alias="E2B_API_KEY")

    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_endpoint: str | None = Field(default=None, alias="LANGCHAIN_ENDPOINT")
    langchain_api_key: str | None = Field(default=None, alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="thesis-generator", alias="LANGCHAIN_PROJECT")


def _collect_settings(secret_manager: SecretManager) -> tuple[dict[str, Any], list[str]]:
    required_keys = ["OPENAI_API_KEY", "SCITE_API_KEY"]
    optional_keys = [
        "OPENALEX_MAILTO",
        "E2B_API_KEY",
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_ENDPOINT",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
    ]

    resolved: dict[str, Any] = {}
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for key in required_keys:
        value = secret_manager.get(key)
        if value:
            resolved[key] = value
        else:
            missing_required.append(key)

    if missing_required:
        logger.error("Missing required environment variables: %s", ", ".join(missing_required))
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_required)}")

    for key in optional_keys:
        value = secret_manager.get(key)
        if value:
            resolved[key] = value
        else:
            missing_optional.append(key)

    return resolved, missing_optional


def load_settings(
    *, secret_manager: SecretManager | None = None, warn_optional: bool = True
) -> Settings:
    """Load settings exclusively through the provided secret manager."""

    manager = secret_manager or InMemorySecretManager(allow_env_fallback=True)
    data, missing_optional = _collect_settings(manager)

    if warn_optional and missing_optional:
        logger.warning(
            "Optional environment variables are not set; features may be limited: %s",
            ", ".join(missing_optional),
        )

    return Settings(**data)


def validate_environment(
    *,
    secret_manager: SecretManager | None = None,
    warn_optional: bool = True,
    exit_on_error: bool = False,
) -> Settings:
    """Validate environment setup and optionally exit on missing required keys."""

    try:
        settings = load_settings(secret_manager=secret_manager, warn_optional=warn_optional)
    except RuntimeError as exc:
        if exit_on_error:
            raise SystemExit(1) from exc
        raise

    logger.info("Environment variables resolved successfully.")
    return settings
