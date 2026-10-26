from typing import Any
import httpx

class OpenAICompatibleClient:
    """Small client for Ollama or vLLM OpenAI-compatible endpoints."""

    def __init__(self, base_url: str, api_key: str = "EMPTY", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def models(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/models", headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def chat(self, model: str, prompt: str, max_tokens: int = 128) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()
