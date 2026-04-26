import os
import pytest
from unittest.mock import MagicMock, patch
from services.llm_service import generate_document


SAMPLE_PROMPT = "Generate a 3-Day Pay or Quit notice for Jane Doe at 123 Main St."


def _mock_openai_response(text: str):
    mock_message = MagicMock()
    mock_message.content = text
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def test_generate_document_returns_text(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    with patch("services.llm_service.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = (
            _mock_openai_response("NOTICE TO PAY OR QUIT\n\nTo: Jane Doe")
        )
        result = generate_document(SAMPLE_PROMPT)

    assert result == "NOTICE TO PAY OR QUIT\n\nTo: Jane Doe"


def test_generate_document_uses_model_from_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o")

    with patch("services.llm_service.OpenAI") as MockClient:
        mock_create = MockClient.return_value.chat.completions.create
        mock_create.return_value = _mock_openai_response("doc text")
        generate_document(SAMPLE_PROMPT)

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "openai/gpt-4o"
        assert call_kwargs["max_tokens"] == 4096


def test_generate_document_uses_openrouter_base_url(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    with patch("services.llm_service.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = (
            _mock_openai_response("doc")
        )
        generate_document(SAMPLE_PROMPT)

        init_kwargs = MockClient.call_args.kwargs
        assert init_kwargs["base_url"] == "https://openrouter.ai/api/v1"


def test_generate_document_propagates_api_exception(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    with patch("services.llm_service.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.side_effect = Exception("API error")
        with pytest.raises(Exception, match="API error"):
            generate_document(SAMPLE_PROMPT)


def test_generate_document_raises_if_api_key_missing(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

    with pytest.raises(KeyError):
        generate_document(SAMPLE_PROMPT)
