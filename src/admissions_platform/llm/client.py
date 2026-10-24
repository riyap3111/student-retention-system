"""LLM client abstraction.

One interface (`LLMClient.extract_structured`), two implementations:
`GeminiClient` for real calls, `FakeLLMClient` for tests — the same
mockable-external-dependency pattern already proven for Google Cloud
Storage in the sibling Student Retention System project. No test in this
project ever makes a real network call to Gemini.

Every caller asks for a specific Pydantic model back (`response_model`),
using Gemini's schema-constrained JSON output rather than parsing free-text
— the extraction, validation, and rules-parsing modules all get back a
typed, already-validated object, not a string to regex apart.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "gemini-2.5-flash"


class LLMClient(ABC):
    @abstractmethod
    def extract_structured(
        self,
        prompt: str,
        response_model: type[T],
        *,
        pdf_bytes: bytes | None = None,
        text: str | None = None,
    ) -> T:
        """Sends `prompt` (plus an optional PDF or extra text block) to the
        model and returns a validated instance of `response_model`.
        Exactly one of pdf_bytes/text is expected per call in practice, but
        both are accepted in case a prompt needs both a document and extra
        context text."""
        raise NotImplementedError


class GeminiClient(LLMClient):
    """Real Gemini calls. PDFs are sent directly (Gemini's native
    multimodal PDF understanding) — no separate OCR step, which is both
    simpler and more robust than traditional OCR-then-regex extraction."""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        from google import (
            genai,  # imported lazily so FakeLLMClient-only tests never need the SDK installed
        )

        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is not set and no api_key was passed to GeminiClient.")
        self._genai = genai
        self.client = genai.Client(api_key=key)
        self.model = model

    def extract_structured(
        self,
        prompt: str,
        response_model: type[T],
        *,
        pdf_bytes: bytes | None = None,
        text: str | None = None,
    ) -> T:
        from google.genai import types

        contents: list = [prompt]
        if pdf_bytes is not None:
            contents.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))
        if text is not None:
            contents.append(text)

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_model,
            ),
        )
        if response.parsed is None:
            raise ValueError(
                f"Gemini response could not be parsed into {response_model.__name__}: {response.text!r}"
            )
        return response.parsed


class FakeLLMClient(LLMClient):
    """Returns pre-programmed responses in order, and records every call
    (prompt, response_model, whether a PDF/text was attached) so tests can
    assert on what was actually asked, not just what came back."""

    def __init__(self, responses: list[BaseModel] | None = None):
        self._responses = list(responses or [])
        self.calls: list[dict] = []

    def queue(self, response: BaseModel) -> None:
        self._responses.append(response)

    def extract_structured(
        self,
        prompt: str,
        response_model: type[T],
        *,
        pdf_bytes: bytes | None = None,
        text: str | None = None,
    ) -> T:
        self.calls.append(
            {
                "prompt": prompt,
                "response_model": response_model,
                "had_pdf": pdf_bytes is not None,
                "had_text": text is not None,
            }
        )
        if not self._responses:
            raise AssertionError(
                f"FakeLLMClient.extract_structured called for {response_model.__name__} "
                "with no queued response left."
            )
        response = self._responses.pop(0)
        if not isinstance(response, response_model):
            # AssertionError, not TypeError: this is a test-helper misuse
            # (wrong fixture queued), the standard pytest idiom — not a
            # production type-contract violation.
            raise AssertionError(  # noqa: TRY004
                f"Queued response is {type(response).__name__}, but caller requested {response_model.__name__}."
            )
        return response


def get_llm_client() -> LLMClient:
    """Default factory: a real GeminiClient if GEMINI_API_KEY is set,
    otherwise raises — callers in request paths should use this; tests
    should construct a FakeLLMClient directly instead of calling this."""
    return GeminiClient()
