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


def test_limit_defaults(monkeypatch):
    for name in ("CLAUDE_MAX_TOKENS", "AGENT_MAX_STEPS", "MAX_MESSAGES", "MAX_MESSAGE_CHARS", "FAQ_MIN_SCORE"):
        monkeypatch.delenv(name, raising=False)
    s = Settings(_env_file=None, anthropic_api_key="x")
    assert (s.claude_max_tokens, s.agent_max_steps, s.max_messages, s.max_message_chars, s.faq_min_score) == (
        1024, 4, 4, 500, 0.82,
    )


def test_limits_from_env(monkeypatch):
    monkeypatch.setenv("CLAUDE_MAX_TOKENS", "256")
    monkeypatch.setenv("AGENT_MAX_STEPS", "2")
    monkeypatch.setenv("FAQ_MIN_SCORE", "0.8")
    s = Settings(_env_file=None, anthropic_api_key="x")
    assert (s.claude_max_tokens, s.agent_max_steps, s.faq_min_score) == (256, 2, 0.8)


@pytest.mark.parametrize(
    "name,value",
    [("CLAUDE_MAX_TOKENS", "0"), ("AGENT_MAX_STEPS", "-1"), ("MAX_MESSAGE_CHARS", "0"), ("MAX_MESSAGES", "0"), ("FAQ_MIN_SCORE", "1.5")],
)
def test_invalid_limit_fails_fast(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError, match=name.lower()):
        Settings(_env_file=None, anthropic_api_key="x")
