
import httpx

from app.ai.llm.base import LLMService
from app.core.config import settings


class OpenRouterProvider(LLMService):
    """OpenRouter implementation of the shared LLM interface."""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.api_key = (
            api_key
            if api_key is not None
            else settings.openrouter_api_key
        )
        self.model = model if model is not None else settings.llm_model
        self.timeout = timeout
        self.transport = transport

    async def generate(
        self,
        messages: list[dict],
        **kwargs,
    ) -> str:
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is missing. "
                "Configure OPENROUTER_API_KEY."
            )

        if not self.model:
            raise ValueError(
                "LLM model is missing. Configure LLM_MODEL."
            )

        if not messages:
            raise ValueError("messages cannot be empty.")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 250,
        }

        # Allow explicit caller settings to override defaults.
        payload.update(kwargs)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
            transport=self.transport,
        ) as client:
            response = await client.post(
                self.API_URL,
                headers=headers,
                json=payload,
            )

        response.raise_for_status()
        data = response.json()

        try:
            choice = data["choices"][0]
            message = choice["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                "OpenRouter returned an unexpected response format."
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                "OpenRouter returned an empty or non-text response."
            )

        return content.strip()
