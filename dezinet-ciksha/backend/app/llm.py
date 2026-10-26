import httpx
from .config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL

async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": OLLAMA_EMBED_MODEL, "input": text}
        )
        response.raise_for_status()
        data = response.json()
        vectors = data.get("embeddings")
        if not vectors:
            # Compatibility with older Ollama API versions.
            old = await client.post(f"{OLLAMA_BASE_URL}/api/embeddings",
                                    json={"model": OLLAMA_EMBED_MODEL, "prompt": text})
            old.raise_for_status()
            return old.json()["embedding"]
        return vectors[0]

async def generate(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_CHAT_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.1}}
        )
        response.raise_for_status()
        return response.json().get("response", "")
