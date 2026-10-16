import pytest
from pydantic import ValidationError

from app.settings import Settings


def test_missing_api_key_fails_fast(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValidationError, match="anthropic_api_key"):
        Settings(_env_file=None)


def test_effort_valid_value_accepted():
    assert Settings(_env_file=None, anthropic_api_key="x", claude_effort="low").claude_effort == "low"


def test_effort_empty_is_unset(monkeypatch):
    monkeypatch.setenv("CLAUDE_EFFORT", "")
    assert Settings(_env_file=None, anthropic_api_key="x").claude_effort is None


def test_effort_unknown_value_fails_fast(monkeypatch):
    monkeypatch.setenv("CLAUDE_EFFORT", "turbo")
    with pytest.raises(ValidationError, match="claude_effort"):
        Settings(_env_file=None, anthropic_api_key="x")


def test_logging_identity_defaults(monkeypatch):
    monkeypatch.delenv("LOG_ID", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    s = Settings(_env_file=None, anthropic_api_key="x")
    assert (s.log_id, s.environment) == ("dev", "local")


def test_logging_identity_from_env(monkeypatch):
    monkeypatch.setenv("LOG_ID", "vadym")
    monkeypatch.setenv("ENVIRONMENT", "prod")
    s = Settings(_env_file=None, anthropic_api_key="x")
    assert (s.log_id, s.environment) == ("vadym", "prod")
