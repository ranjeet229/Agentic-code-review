import httpx
import pytest

from reviewmate.provider import GeminiProvider, ProviderError, provider_from_env


def test_missing_key_has_actionable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="GEMINI_API_KEY"):
        provider_from_env()


def test_timeout_is_reported_without_a_review(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: object, **kwargs: object) -> object:
        raise httpx.TimeoutException("slow")

    monkeypatch.setattr(httpx, "post", timeout)
    with pytest.raises(ProviderError, match="timed out"):
        GeminiProvider("key", "model").review("diff")


def test_connection_error_is_reported_without_a_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def connection_error(*args: object, **kwargs: object) -> object:
        raise httpx.ConnectError("connection reset")

    monkeypatch.setattr(httpx, "post", connection_error)
    with pytest.raises(ProviderError, match="Could not connect to Gemini"):
        GeminiProvider("key", "model").review("diff")


def test_gemini_json_fence_is_unwrapped() -> None:
    assert GeminiProvider._json_text("```json\n{\"findings\": []}\n```") == '{"findings": []}'
