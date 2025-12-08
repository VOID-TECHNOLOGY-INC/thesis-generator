from __future__ import annotations

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    scite_api_key: str = Field(..., alias="SCITE_API_KEY")
    openalex_mailto: str | None = Field(default=None, alias="OPENALEX_MAILTO")
    e2b_api_key: str | None = Field(default=None, alias="E2B_API_KEY")

    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_endpoint: str | None = Field(default=None, alias="LANGCHAIN_ENDPOINT")
    langchain_api_key: str | None = Field(default=None, alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="thesis-generator", alias="LANGCHAIN_PROJECT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


def load_settings() -> Settings:
    """Load settings from environment, failing fast on missing keys."""

    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        missing_vars = [".".join(map(str, err.get("loc", ()))) for err in exc.errors()]
        missing = ", ".join(filter(None, missing_vars))
        detail = f"Missing required environment variables: {missing or 'unknown'}"
        raise RuntimeError(detail) from exc
