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
