import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .config import MODEL_NAME, TENANT_BUDGET_USD
from .metrics import REQUESTS, REQUEST_LATENCY, TTFT, ITL, TOKENS, COST, TENANT_SPEND, metrics_response
from .schemas import ChatRequest, FeedbackRequest
from .store import add_feedback, add_usage, tenant_usage, all_feedback
from .telemetry import tracer, current_trace_id
from .usage import estimate_tokens, calculate_usage

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Task 12 — LLM Observability", version="0.1.0", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(payload: ChatRequest):
    started = time.perf_counter()
    with tracer.start_as_current_span("ai_request") as root:
        root.set_attribute("user.id", payload.user_id)
        root.set_attribute("tenant.id", payload.tenant_id)
        root.set_attribute("http.route", payload.endpoint)
        root.set_attribute("llm.model", MODEL_NAME)
        trace_id = current_trace_id() or uuid.uuid4().hex
        try:
            # Example budget check. For real deployments use atomic Redis-backed accounting
            # and reserve budget before dispatching the model request.
            current_spend = await tenant_usage(payload.tenant_id)
            if current_spend >= TENANT_BUDGET_USD:
                REQUESTS.labels(payload.endpoint, "budget_rejected").inc()
                raise HTTPException(status_code=429, detail="Tenant AI spend budget exceeded")

            with tracer.start_as_current_span("query_rewrite") as span:
                span.set_attribute("pipeline.step", "query_rewrite")
                query = payload.message.strip()

            with tracer.start_as_current_span("vector_retrieval") as span:
                span.set_attribute("pipeline.step", "vector_retrieval")
                span.set_attribute("retrieval.demo_mode", True)
                context = f"Demo retrieved context for query: {query[:300]}"

            with tracer.start_as_current_span("reranker") as span:
                span.set_attribute("pipeline.step", "reranker")
                span.set_attribute("reranker.candidate_count", 1)

            with tracer.start_as_current_span("prompt_construction") as span:
                prompt = f"Answer clearly using the context below.\nContext: {context}\nQuestion: {query}"
                span.set_attribute("prompt.template_version", "v1")
                span.set_attribute("prompt.length", len(prompt))

            with tracer.start_as_current_span("llm_generation") as span:
                span.set_attribute("llm.model", MODEL_NAME)
                span.set_attribute("llm.temperature", 0.0)
                # Offline deterministic demo; replace this with your provider's LLM call.
                answer = f"Demo answer based on retrieved context: {query}"
                prompt_tokens = estimate_tokens(prompt)
                completion_tokens = estimate_tokens(answer)
                usage = calculate_usage(prompt_tokens, completion_tokens)
                span.set_attribute("llm.usage.prompt_tokens", prompt_tokens)
                span.set_attribute("llm.usage.completion_tokens", completion_tokens)
                span.set_attribute("llm.cost.usd", usage.cost_usd)

            spent = await add_usage(payload.tenant_id, usage.cost_usd)
            TENANT_SPEND.labels(payload.tenant_id).set(spent)
            TOKENS.labels("prompt", MODEL_NAME).inc(prompt_tokens)
            TOKENS.labels("completion", MODEL_NAME).inc(completion_tokens)
            COST.labels(payload.tenant_id, payload.endpoint).inc(usage.cost_usd)
            elapsed = time.perf_counter() - started
            REQUEST_LATENCY.labels(payload.endpoint).observe(elapsed)
            REQUESTS.labels(payload.endpoint, "success").inc()
            root.set_attribute("trace.id", trace_id)
            root.set_attribute("llm.usage.prompt_tokens", prompt_tokens)
            root.set_attribute("llm.usage.completion_tokens", completion_tokens)
            root.set_attribute("llm.cost.usd", usage.cost_usd)
            return {
                "trace_id": trace_id,
                "answer": answer,
                "model": MODEL_NAME,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "estimated_cost_usd": usage.cost_usd,
                    "tenant_spend_usd": round(spent, 10),
                },
                "latency": {"total_seconds": round(elapsed, 6), "ttft_seconds": None, "itl_seconds": None},
                "note": "Offline demo response; connect a streaming LLM provider to measure real TTFT/ITL."
            }
        except HTTPException:
            raise
        except Exception as exc:
            root.record_exception(exc)
            root.set_status(Status(StatusCode.ERROR, str(exc)))
            REQUESTS.labels(payload.endpoint, "error").inc()
            raise

@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest):
    # Demo token stream for exercising TTFT and ITL instrumentation.
    async def events():
        start = time.perf_counter()
        first_token_time = None
        previous = None
        chunks = ["Observability", " makes", " AI", " pipelines", " measurable."]
        with tracer.start_as_current_span("ai_stream_request") as span:
            span.set_attribute("user.id", payload.user_id)
            span.set_attribute("tenant.id", payload.tenant_id)
            span.set_attribute("llm.model", MODEL_NAME)
            tid = current_trace_id() or uuid.uuid4().hex
            for token in chunks:
                await asyncio.sleep(0.03)  # simulate provider streaming
                now = time.perf_counter()
                if first_token_time is None:
                    first_token_time = now
                    TTFT.labels("/chat/stream").observe(now - start)
                if previous is not None:
                    ITL.labels("/chat/stream").observe(now - previous)
                previous = now
                yield f"data: {json.dumps({'trace_id': tid, 'token': token})}\n\n"
            elapsed = time.perf_counter() - start
            REQUEST_LATENCY.labels("/chat/stream").observe(elapsed)
            REQUESTS.labels("/chat/stream", "success").inc()
            span.set_attribute("llm.ttft_seconds", (first_token_time - start) if first_token_time else 0)
            span.set_attribute("llm.total_seconds", elapsed)
            yield f"data: {json.dumps({'done': True, 'total_seconds': round(elapsed, 6)})}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")

@app.post("/feedback", status_code=201)
async def feedback(payload: FeedbackRequest):
    try:
        payload.model_validate_feedback()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    record = {
        "feedback_id": uuid.uuid4().hex,
        "trace_id": payload.trace_id,
        "rating": payload.rating,
        "correction": payload.correction,
        "created_at": time.time(),
    }
    await add_feedback(record)
    with tracer.start_as_current_span("user_feedback") as span:
        span.set_attribute("feedback.trace_id", payload.trace_id)
        if payload.rating:
            span.set_attribute("feedback.rating", payload.rating)
    return record

@app.get("/feedback")
async def list_feedback():
    return {"items": await all_feedback()}

@app.get("/usage/{tenant_id}")
async def usage(tenant_id: str):
    return {"tenant_id": tenant_id, "estimated_spend_usd": round(await tenant_usage(tenant_id), 10),
            "budget_usd": TENANT_BUDGET_USD}

@app.get("/metrics")
async def prometheus_metrics():
    return metrics_response()
