from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from redis.asyncio import Redis
from redis.exceptions import RedisError
from app.config import settings
from app.memory import MemoryManager
from app.models import ChatRequest, ChatResponse
from app.providers import get_provider
from app.store import RedisSessionStore
from app.token_budget import TokenBudget

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.store = RedisSessionStore(app.state.redis)
    app.state.provider = get_provider()
    app.state.budget = TokenBudget(settings.max_history_tokens)
    app.state.memory = MemoryManager(app.state.budget)
    try:
        yield
    finally:
        await app.state.redis.aclose()

app = FastAPI(title="Task 08 — Conversational Memory", version="0.1.0", lifespan=lifespan)

@app.get("/health")
async def health():
    try:
        await app.state.redis.ping()
        return {"status": "ok", "redis": "connected"}
    except (RedisError, AttributeError):
        raise HTTPException(status_code=503, detail="Redis unavailable")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        store = app.state.store
        all_messages = await store.load_messages(request.session_id)
        prior_history = [m for m in all_messages if m.get("role") in ("user", "assistant", "system")]
        summary = await store.load_summary(request.session_id)
        entities = await store.load_entities(request.session_id)

        # Rewrite before retrieval/generation so follow-ups are independently interpretable.
        standalone_query = await app.state.provider.rewrite_query(prior_history, request.message)

        # Include the current user message for memory extraction/context, but don't persist until response is ready.
        working_messages = prior_history + [{"role": "user", "content": request.message}]
        context = app.state.memory.build_context(request.memory_strategy, working_messages, summary, entities)

        if request.memory_strategy == "summary_buffer":
            older = working_messages[:-6] if len(working_messages) > 6 else []
            if older:
                context["summary"] = await app.state.provider.summarize(older, summary)
        context["strategy"] = request.memory_strategy
        history_tokens = app.state.budget.count_messages(context["messages"])
        answer = await app.state.provider.answer(standalone_query, context)

        await store.save_turn(
            request.session_id, request.message, answer,
            summary=context.get("summary") if request.memory_strategy == "summary_buffer" else None,
            entities=context.get("entities") if request.memory_strategy == "entity" else None,
        )
        await store.refresh_ttl(request.session_id)
        return ChatResponse(
            session_id=request.session_id, answer=answer, standalone_query=standalone_query,
            memory_strategy=request.memory_strategy, history_tokens=history_tokens,
            history_messages_used=len(context["messages"]),
        )
    except RedisError:
        raise HTTPException(status_code=503, detail="Redis unavailable; start Redis and retry")
    except Exception as exc:
        # Avoid leaking internal exception details to clients.
        raise HTTPException(status_code=500, detail="Chat processing failed") from exc

@app.get("/sessions/{session_id}")
async def inspect_session(session_id: str):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", session_id):
        raise HTTPException(status_code=422, detail="Invalid session_id")
    try:
        store = app.state.store
        messages = await store.load_messages(session_id)
        return {
            "session_id": session_id,
            "messages": messages,
            "summary": await store.load_summary(session_id),
            "entities": await store.load_entities(session_id),
        }
    except RedisError:
        raise HTTPException(status_code=503, detail="Redis unavailable")

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", session_id):
        raise HTTPException(status_code=422, detail="Invalid session_id")
    try:
        deleted = await app.state.store.delete_session(session_id)
        return {"session_id": session_id, "deleted_keys": deleted}
    except RedisError:
        raise HTTPException(status_code=503, detail="Redis unavailable")
