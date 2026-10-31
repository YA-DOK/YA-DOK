from __future__ import annotations

import json

import httpx
import pytest

from app.ai.f04.provider import (
    InvalidModelOutput,
    ModelSettings,
    OpenRouterTextModel,
    ProviderUnavailable,
)


@pytest.mark.asyncio
async def test_openrouter_http_payload_strict_private_and_single_call():
    bodies = []

    def handle(request: httpx.Request):
        bodies.append(json.loads(request.content))
        assert request.headers["Authorization"] == "Bearer fake-test-key"
        return httpx.Response(200, json={
            "model": "openai/gpt-6-luna",
            "choices": [{"message": {"content": json.dumps({
                "intent": "history_question", "answerability": "answered",
                "fact_ids": ["fever__0"], "reply": "بدأت من يومين",
                "parts": [{"span": "السخونية من امتى", "answerability": "answered", "fact_ids": ["fever__0"], "reply": "بدأت من يومين"}],
            })}}],
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        provider = OpenRouterTextModel(ModelSettings(api_key="fake-test-key"), client)
        result, model = await provider.generate(
            messages=[{"role": "system", "content": "Patient"}],
            allowed_fact_ids=["fever__0"], session_key="session-1",
        )
    assert result.fact_ids == ["fever__0"]
    assert model == "openai/gpt-6-luna"
    assert len(bodies) == 1
    assert bodies[0]["provider"]["zdr"] is True
    assert bodies[0]["provider"]["data_collection"] == "deny"
    assert bodies[0]["provider"]["require_parameters"] is True
    assert bodies[0]["response_format"]["json_schema"]["strict"] is True
    schema = bodies[0]["response_format"]["json_schema"]["schema"]
    assert "parts" in schema["required"]
    assert schema["properties"]["parts"]["items"]["additionalProperties"] is False
    assert result.parts[0].span == "السخونية من امتى"


@pytest.mark.asyncio
async def test_http_provider_failure_does_not_leak_raw_response():
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(429, text="Sensitive incident: patient's full record")
    )) as client:
        provider = OpenRouterTextModel(ModelSettings(api_key="fake-test-key"), client)
        with pytest.raises(ProviderUnavailable) as exc:
            await provider.generate(messages=[], allowed_fact_ids=["fever__0"], session_key="x")
        assert "Sensitive incident" not in str(exc.value)


@pytest.mark.asyncio
async def test_invalid_model_json_is_rejected():
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"choices": [{"message": {"content": "not-json"}}]})
    )) as client:
        provider = OpenRouterTextModel(ModelSettings(api_key="fake-test-key"), client)
        with pytest.raises(InvalidModelOutput):
            await provider.generate(messages=[], allowed_fact_ids=["fever__0"], session_key="x")
