import pytest

from thesis_generator.config import load_settings


def test_load_settings_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SEMANTIC_SCHOLAR_API_KEY", raising=False)
    monkeypatch.delenv("SCITE_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as err:
        load_settings()

    message = str(err.value)
    assert "OPENAI_API_KEY" in message
    assert "SEMANTIC_SCHOLAR_API_KEY" in message
    assert "SCITE_API_KEY" in message


def test_load_settings_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "test-scholar")
    monkeypatch.setenv("SCITE_API_KEY", "test-scite")

    settings = load_settings()

    assert settings.openai_api_key == "test-openai"
    assert settings.semantic_scholar_api_key == "test-scholar"
    assert settings.scite_api_key == "test-scite"
