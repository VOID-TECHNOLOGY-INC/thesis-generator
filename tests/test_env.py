import pytest

from thesis_generator.config import load_settings
from thesis_generator.security import InMemorySecretManager


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
