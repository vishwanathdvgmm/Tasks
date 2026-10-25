import asyncio, json, logging, time, uuid
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import settings
from app.database import close_db, engine, init_db
from app.dependencies import rate_limit
from app.schemas import ChatRequest, EmbeddingRequest, EmbeddingResponse, EmbeddingItem, HealthResponse
from app.services import mock_embedding, mock_token_stream

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("async-ai-service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                   allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type", "X-Request-ID"])

@app.middleware("http")
async def request_timing(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    elapsed = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    logger.info(json.dumps({"event":"request_complete","request_id":request_id,
        "method":request.method,"path":request.url.path,"status_code":response.status_code,
        "duration_ms":elapsed}))
    return response

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error":{"type":"validation_error",
        "message":"Request validation failed","details":jsonable_encoder(exc.errors())}})

@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code,
        content={"error":{"type":"http_error","message":str(exc.detail)}}, headers=exc.headers)

@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    logger.exception("Unhandled application error")
    return JSONResponse(status_code=500, content={"error":{"type":"internal_server_error",
        "message":"An unexpected error occurred"}})

@app.get("/health", response_model=HealthResponse, tags=["operations"])
async def health():
    return HealthResponse(status="ok", service=settings.app_name)

@app.get("/ready", response_model=HealthResponse, tags=["operations"])
async def ready():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return HealthResponse(status="ok", service=settings.app_name)
    except Exception:
        raise HTTPException(status_code=503, detail="Database is not ready")

@app.get("/v1/status", tags=["operations"])
async def status(_client: str = Depends(rate_limit)):
    return {"status":"ok","model":settings.model_name,"provider":"mock"}

@app.post("/v1/chat/completions", tags=["inference"])
async def chat(payload: ChatRequest, request: Request, _client: str = Depends(rate_limit)):
    request_id = payload.request_id or request.headers.get("X-Request-ID") or str(uuid.uuid4())
    if not payload.stream:
        parts = []
        async for token in mock_token_stream(payload.prompt, payload.max_tokens):
            if await request.is_disconnected():
                break
            parts.append(token)
        return {"id":request_id,"object":"chat.completion","model":settings.model_name,
            "choices":[{"index":0,"message":{"role":"assistant","content":"".join(parts).strip()},
                        "finish_reason":"stop"}]}

    async def events():
        try:
            yield f"event: metadata\ndata: {json.dumps({'id':request_id,'model':settings.model_name})}\n\n"
            async for token in mock_token_stream(payload.prompt, payload.max_tokens):
                if await request.is_disconnected():
                    logger.info(json.dumps({"event":"stream_disconnected","request_id":request_id}))
                    break
                yield f"data: {json.dumps({'token':token})}\n\n"
            else:
                yield "data: [DONE]\n\n"
        except asyncio.CancelledError:
            logger.info(json.dumps({"event":"stream_cancelled","request_id":request_id}))
            raise
    return StreamingResponse(events(), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@app.post("/v1/embeddings", response_model=EmbeddingResponse, tags=["inference"])
async def embeddings(payload: EmbeddingRequest, _client: str = Depends(rate_limit)):
    inputs = [payload.input] if isinstance(payload.input, str) else payload.input
    return EmbeddingResponse(data=[EmbeddingItem(index=i, embedding=mock_embedding(s))
                                   for i, s in enumerate(inputs)])
