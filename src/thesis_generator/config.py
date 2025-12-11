from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from thesis_generator.security import InMemorySecretManager, SecretManager


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


def _collect_settings(secret_manager: SecretManager) -> dict[str, Any]:
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
    missing: list[str] = []

    for key in required_keys:
        value = secret_manager.get(key)
        if value:
            resolved[key] = value
        else:
            missing.append(key)

    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    for key in optional_keys:
        value = secret_manager.get(key)
        if value is not None:
            resolved[key] = value

    return resolved


def load_settings(*, secret_manager: SecretManager | None = None) -> Settings:
    """Load settings exclusively through the provided secret manager."""

    manager = secret_manager or InMemorySecretManager(allow_env_fallback=True)
    data = _collect_settings(manager)
    return Settings(**data)
