import os

APP_NAME = os.getenv("APP_NAME", "task12-observability")
MODEL_NAME = os.getenv("MODEL_NAME", "demo-model")
# Demo rates are illustrative USD per 1M tokens. Replace with current provider pricing.
INPUT_USD_PER_MILLION = float(os.getenv("INPUT_USD_PER_MILLION", "0.15"))
OUTPUT_USD_PER_MILLION = float(os.getenv("OUTPUT_USD_PER_MILLION", "0.60"))
TENANT_BUDGET_USD = float(os.getenv("TENANT_BUDGET_USD", "5.00"))
REDIS_URL = os.getenv("REDIS_URL", "")
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
