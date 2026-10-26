from contextlib import asynccontextmanager
import os

import httpx
import psycopg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        async with psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
            await conn.execute("SELECT 1")
        await app.state.cache.ping()
    except Exception:
        await app.state.cache.aclose()
        raise
    yield
    await app.state.cache.aclose()

app = FastAPI(title="Task 14 AI Infrastructure API", version="1.0.0", lifespan=lifespan)

class NoteIn(BaseModel):
    content: str = Field(min_length=1, max_length=10000)

class GenerateIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    model: str | None = None

@app.get("/")
async def root():
    return {"service": "task14-ai-stack", "docs": "/docs", "health": "/health"}

@app.get("/health")
async def health():
    """Liveness probe; dependency readiness is exposed separately."""
    return {"status": "ok"}

@app.get("/ready")
async def ready():
    status = {"api": "ok", "postgres": "ok", "redis": "ok", "ollama": "unknown"}
    try:
        async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
            await conn.execute("SELECT 1")
    except Exception as exc:
        status["postgres"] = "error"
        raise HTTPException(status_code=503, detail=status) from exc
    try:
        await app.state.cache.ping()
    except Exception as exc:
        status["redis"] = "error"
        raise HTTPException(status_code=503, detail=status) from exc
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
        status["ollama"] = "ok"
    except Exception:
        status["ollama"] = "unavailable"
    return status

@app.post("/notes", status_code=201)
async def create_note(note: NoteIn):
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        cursor = await conn.execute(
            "INSERT INTO service_notes (content) VALUES (%s) RETURNING id, content, created_at",
            (note.content,),
        )
        row = await cursor.fetchone()
        await conn.commit()
    return {"id": row[0], "content": row[1], "created_at": row[2]}

@app.get("/notes")
async def list_notes():
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        cursor = await conn.execute(
            "SELECT id, content, created_at FROM service_notes ORDER BY id DESC LIMIT 100"
        )
        rows = await cursor.fetchall()
    return [{"id": r[0], "content": r[1], "created_at": r[2]} for r in rows]

@app.post("/generate")
async def generate(body: GenerateIn):
    cache_key = f"generation:{body.model or OLLAMA_MODEL}:{body.prompt}"
    cached = await app.state.cache.get(cache_key)
    if cached is not None:
        return {"model": body.model or OLLAMA_MODEL, "response": cached, "cached": True}
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": body.model or OLLAMA_MODEL, "prompt": body.prompt, "stream": False},
            )
            response.raise_for_status()
            answer = response.json()["response"]
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Ollama unavailable; ensure the model is pulled.") from exc
    await app.state.cache.set(cache_key, answer, ex=3600)
    return {"model": body.model or OLLAMA_MODEL, "response": answer, "cached": False}
