import pytest

from thesis_generator.config import load_settings


def test_load_settings_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SCITE_API_KEY", raising=False)
    monkeypatch.delenv("OPENALEX_MAILTO", raising=False)

    with pytest.raises(RuntimeError) as err:
        load_settings()

    message = str(err.value)
    assert "OPENAI_API_KEY" in message
    assert "SCITE_API_KEY" in message


def test_load_settings_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("SCITE_API_KEY", "test-scite")
    monkeypatch.setenv("OPENALEX_MAILTO", "you@example.com")

    settings = load_settings()

    assert settings.openai_api_key == "test-openai"
    assert settings.scite_api_key == "test-scite"
    assert settings.openalex_mailto == "you@example.com"
