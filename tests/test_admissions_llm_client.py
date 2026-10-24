"""Tests for the LLM client abstraction. FakeLLMClient is what every other
module's tests use instead of a real Gemini call."""
import pytest
from pydantic import BaseModel

from admissions_platform.llm.client import FakeLLMClient, GeminiClient


class _Thing(BaseModel):
    value: str


class _OtherThing(BaseModel):
    other_value: int


def test_fake_llm_client_returns_queued_responses_in_order():
    client = FakeLLMClient(responses=[_Thing(value="first"), _Thing(value="second")])

    assert client.extract_structured("prompt one", _Thing).value == "first"
    assert client.extract_structured("prompt two", _Thing).value == "second"


def test_fake_llm_client_records_every_call():
    client = FakeLLMClient(responses=[_Thing(value="x")])
    client.extract_structured("describe this PDF", _Thing, pdf_bytes=b"%PDF-data")

    assert len(client.calls) == 1
    assert client.calls[0]["prompt"] == "describe this PDF"
    assert client.calls[0]["response_model"] is _Thing
    assert client.calls[0]["had_pdf"] is True
    assert client.calls[0]["had_text"] is False


def test_fake_llm_client_raises_when_queue_is_empty():
    client = FakeLLMClient()
    with pytest.raises(AssertionError):
        client.extract_structured("prompt", _Thing)


def test_fake_llm_client_raises_when_queued_response_is_the_wrong_type():
    client = FakeLLMClient(responses=[_OtherThing(other_value=1)])
    with pytest.raises(AssertionError):
        client.extract_structured("prompt", _Thing)


def test_fake_llm_client_queue_method_appends(monkeypatch):
    client = FakeLLMClient()
    client.queue(_Thing(value="later"))
    assert client.extract_structured("prompt", _Thing).value == "later"


def test_gemini_client_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GeminiClient(api_key=None)
