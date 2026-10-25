import hmac
import time
from collections import defaultdict, deque
from fastapi import Depends, Header, HTTPException, Request, status
from app.config import settings

_buckets: dict[str, deque[float]] = defaultdict(deque)

async def require_api_key(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer API key",
                            headers={"WWW-Authenticate": "Bearer"})
    if not hmac.compare_digest(authorization.removeprefix("Bearer ").strip(), settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key",
                            headers={"WWW-Authenticate": "Bearer"})
    return "authenticated-client"

async def rate_limit(request: Request, _client: str = Depends(require_api_key)) -> str:
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _buckets[ip]
    while bucket and bucket[0] <= now - settings.rate_limit_window_seconds:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded",
                            headers={"Retry-After": str(settings.rate_limit_window_seconds)})
    bucket.append(now)
    return ip
