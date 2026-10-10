from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod

import httpx

from .models import ReviewResponse


class ProviderError(RuntimeError):
    pass


class ModelProvider(ABC):
    @abstractmethod
    def review(self, prompt: str) -> ReviewResponse: ...


class OpenAICompatibleProvider(ModelProvider):
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key, self.base_url, self.model = api_key, base_url.rstrip("/"), model

    def review(self, prompt: str) -> ReviewResponse:
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}, "temperature": 0}
        try:
            response = httpx.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return ReviewResponse.model_validate(json.loads(content))
        except httpx.TimeoutException as exc:
            raise ProviderError("Model request timed out; no review was produced.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise ProviderError("Model rate limit reached; no review was produced.") from exc
            raise ProviderError(f"Model request failed ({exc.response.status_code}); no review was produced.") from exc
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise ProviderError("Model returned malformed JSON; no review was produced.") from exc


def provider_from_env() -> ModelProvider:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ProviderError("Missing GEMINI_API_KEY. Run `reviewmate config` for setup help.")
    return GeminiProvider(key, os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))


class GeminiProvider(ModelProvider):
    """Gemini generateContent adapter, isolated behind the provider interface."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key, self.model = api_key, model

    def review(self, prompt: str) -> ReviewResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
        try:
            response = httpx.post(url, params={"key": self.api_key}, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return ReviewResponse.model_validate(json.loads(content))
        except httpx.TimeoutException as exc:
            raise ProviderError("Gemini request timed out; no review was produced.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise ProviderError("Gemini rate limit reached; no review was produced.") from exc
            raise ProviderError(f"Gemini request failed ({exc.response.status_code}); no review was produced.") from exc
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise ProviderError("Gemini returned malformed JSON; no review was produced.") from exc
