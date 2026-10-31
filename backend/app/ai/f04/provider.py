"""OpenRouter HTTP adapter with schema-constrained output; no provider secrets logged."""
from __future__ import annotations

import json
from dataclasses import dataclass

import httpx
from pydantic import ValidationError

from .contracts import PatientChatResult


class ProviderUnavailable(Exception):
    pass


class InvalidModelOutput(Exception):
    pass


@dataclass(frozen=True)
class ModelSettings:
    api_key: str
    model: str = "openai/gpt-6-luna"
    base_url: str = "https://openrouter.ai/api/v1"
    timeout_seconds: float = 12.0
    max_completion_tokens: int = 650


class OpenRouterTextModel:
    def __init__(self, settings: ModelSettings, client: httpx.AsyncClient) -> None:
        self.settings = settings
        self.client = client

    async def generate(
        self, *, messages: list[dict[str, str]], allowed_fact_ids: list[str], session_key: str
    ) -> tuple[PatientChatResult, str | None]:
        if not self.settings.api_key.strip():
            raise ProviderUnavailable("API key not configured")
        schema = {
            "type": "object", "additionalProperties": False,
            "properties": {
                "intent": {"type": "string", "enum": [
                    "history_question", "examination_request", "investigation_request",
                    "diagnosis_attempt", "management_attempt", "other"]},
                "answerability": {"type": "string", "enum": ["answered", "unknown", "partial", "not_applicable"]},
                "fact_ids": {"type": "array", "items": {"type": "string", "enum": allowed_fact_ids}},
                "reply": {"type": "string"},
                "parts": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "span": {"type": "string"},
                        "answerability": {"type": "string", "enum": ["answered", "unknown"]},
                        "fact_ids": {"type": "array", "items": {"type": "string", "enum": allowed_fact_ids}},
                        "reply": {"type": "string"},
                    },
                    "required": ["span", "answerability", "fact_ids", "reply"],
                }},
            },
            "required": ["intent", "answerability", "fact_ids", "reply", "parts"],
        }
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "max_completion_tokens": self.settings.max_completion_tokens,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "patient_chat", "strict": True, "schema": schema,
            }},
            "session_id": session_key,
            "provider": {
                "require_parameters": True,
                "data_collection": "deny",
                "zdr": True,
                "allow_fallbacks": True,
            },
        }
        try:
            r = await self.client.post(
                f"{self.settings.base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.settings.api_key}", "Content-Type": "application/json"},
                timeout=httpx.Timeout(self.settings.timeout_seconds, connect=2.0),
            )
            r.raise_for_status()
            body = r.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise InvalidModelOutput("No text completion")
            result = PatientChatResult.model_validate(json.loads(content))
            return result, body.get("model") if isinstance(body.get("model"), str) else self.settings.model
        except (httpx.HTTPError, TimeoutError) as exc:
            # Do not include raw provider response; it may contain sensitive prompt fragments.
            raise ProviderUnavailable("Upstream provider failed or timed out") from exc
        except (KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
            raise InvalidModelOutput("Provider returned invalid structured output") from exc
