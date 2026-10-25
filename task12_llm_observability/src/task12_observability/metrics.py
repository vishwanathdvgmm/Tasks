from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

REQUESTS = Counter("llm_requests_total", "LLM requests", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("llm_request_duration_seconds", "Total request duration", ["endpoint"])
TTFT = Histogram("llm_ttft_seconds", "Time to first generated token", ["endpoint"])
ITL = Histogram("llm_inter_token_latency_seconds", "Inter-token latency", ["endpoint"])
TOKENS = Counter("llm_tokens_total", "LLM tokens", ["kind", "model"])
COST = Counter("llm_estimated_cost_usd_total", "Estimated model cost in USD", ["tenant_id", "endpoint"])
TENANT_SPEND = Gauge("llm_tenant_estimated_spend_usd", "In-process cumulative spend by tenant", ["tenant_id"])

def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
