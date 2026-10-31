
import httpx
import pytest
from backend.app.ai.llm.openrouter import OpenRouterProvider


@pytest.mark.anyio
async def test_openrouter_provider_sends_request_and_returns_content():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == (
            "https://openrouter.ai/api/v1/chat/completions"
        )
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Content-Type"] == "application/json"

        payload = __import__("json").loads(request.content)

        assert payload["model"] == "test-model"
        assert payload["messages"] == [
            {"role": "user", "content": "Hello"}
        ]

        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Hello from the fake model!",
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(mock_handler)

    provider = OpenRouterProvider(
        api_key="test-key",
        model="test-model",
        transport=transport,
    )

    result = await provider.generate(
        [{"role": "user", "content": "Hello"}]
    )

    assert result == "Hello from the fake model!"


@pytest.mark.anyio
async def test_openrouter_provider_requires_api_key():
    provider = OpenRouterProvider(api_key="", model="test-model")

    with pytest.raises(ValueError, match="API key is missing"):
        await provider.generate(
            [{"role": "user", "content": "Hello"}]
        )


@pytest.mark.anyio
async def test_openrouter_provider_requires_model():
    provider = OpenRouterProvider(api_key="test-key", model="")

    with pytest.raises(ValueError, match="model is missing"):
        await provider.generate(
            [{"role": "user", "content": "Hello"}]
        )


@pytest.mark.anyio
async def test_openrouter_provider_rejects_empty_messages():
    provider = OpenRouterProvider(
        api_key="test-key",
        model="test-model",
    )

    with pytest.raises(ValueError, match="messages cannot be empty"):
        await provider.generate([])
