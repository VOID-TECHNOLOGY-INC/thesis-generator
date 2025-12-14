import logging
from pathlib import Path

import pytest

from thesis_generator.config import load_settings
from thesis_generator.security import InMemorySecretManager
from thesis_generator.main import run_cli


class _StubGraph:
    def invoke(self, state):  # pragma: no cover - not reached when env missing
        return state


def test_load_settings_requires_secret_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SCITE_API_KEY", raising=False)
    monkeypatch.delenv("OPENALEX_MAILTO", raising=False)

    with pytest.raises(RuntimeError) as err:
        load_settings(secret_manager=InMemorySecretManager())

    message = str(err.value)
    assert "OPENAI_API_KEY" in message
    assert "SCITE_API_KEY" in message


def test_load_settings_pulls_from_vault(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SCITE_API_KEY", raising=False)
    monkeypatch.delenv("OPENALEX_MAILTO", raising=False)

    secrets = {
        "OPENAI_API_KEY": "vault-openai",
        "SCITE_API_KEY": "vault-scite",
        "OPENALEX_MAILTO": "vault@example.com",
    }
    settings = load_settings(secret_manager=InMemorySecretManager(secrets))

    assert settings.openai_api_key == "vault-openai"
    assert settings.scite_api_key == "vault-scite"
    assert settings.openalex_mailto == "vault@example.com"


def test_load_settings_warns_on_optional_missing(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("SCITE_API_KEY", "test-scite")
    monkeypatch.delenv("OPENALEX_MAILTO", raising=False)
    monkeypatch.delenv("E2B_API_KEY", raising=False)

    caplog.set_level(logging.WARNING)
    load_settings()

    messages = " | ".join(record.message for record in caplog.records)
    assert "Optional environment variables are not set" in messages
    assert "OPENALEX_MAILTO" in messages


def test_cli_exits_with_error_when_required_env_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SCITE_API_KEY", raising=False)

    caplog.set_level(logging.ERROR)
    with pytest.raises(SystemExit) as excinfo:
        run_cli(
            ["--topic", "Env failure", "--output", str(tmp_path / "out.md")],
            graph_factory=lambda: _StubGraph(),
        )

    assert excinfo.value.code == 1
    assert any("Missing required environment variables" in record.message for record in caplog.records)
