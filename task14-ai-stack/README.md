# Task 14 — Containerized AI Pipeline

A reproducible FastAPI stack with PostgreSQL + pgvector, Redis, and Ollama, built around a multi-stage `uv` Dockerfile.

## Prerequisites

- Docker Engine and Docker Compose v2
- At least 8 GB RAM recommended for local Ollama inference; model storage is several GB
- For NVIDIA GPU inference, install NVIDIA drivers and NVIDIA Container Toolkit on the host first

## Run locally

```bash
cp .env.example .env
# Edit .env and replace POSTGRES_PASSWORD with a strong random value.
docker-compose up --build -d
# Download the default model (first download can take several minutes)
docker-compose exec ollama ollama pull qwen2.5:3b
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Open interactive API docs at `http://localhost:8000/docs`.

## Try endpoints

```bash
curl -X POST http://localhost:8000/notes \
  -H 'Content-Type: application/json' \
  -d '{"content":"Container stack is running"}'

curl http://localhost:8000/notes

curl -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Explain Docker multi-stage builds in two sentences."}'
```

## Architecture

- `api`: FastAPI; non-root `appuser`, read-only root filesystem, no-new-privileges, HTTP health check
- `postgres`: PostgreSQL 16 with pgvector extension, persistent volume, `pg_isready` health check
- `redis`: persistent AOF cache, `redis-cli ping` health check
- `ollama`: local model server and persistent model volume; model is pulled explicitly after startup
- `backend`: private Compose bridge network; only the API port is published by default

## Useful commands

```bash
docker-compose ps
docker-compose logs -f api
docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\\dx'
docker-compose down                 # stop containers; preserve volumes
docker-compose down -v              # DESTRUCTIVE: remove persistent data and model volume
```

## Security notes

- `.env` is excluded from the Docker build context and Git. Never commit it.
- `.env.example` contains placeholders only. Use a secret manager or your platform's secret injection for production.
- Database and Redis ports are not published to the host.
- Rotate credentials if they are exposed. Restrict inbound VPS firewall rules to the required API/reverse-proxy ports and put TLS/authentication in front of a public deployment.
- Compose environment interpolation passes the database password to the API connection URL. For higher-security deployments, use Docker secrets or your platform's secret manager and construct the URL at runtime.

## Image size target

The Dockerfile separates dependency installation from the runtime image, uses a BuildKit cache mount for uv, and copies only the virtual environment and application into the final stage. Measure the actual result with `docker image ls task14-ai-api:local`; a strict `<200 MB` target depends on the installed wheels and base-image architecture and must be verified on the build host.

## GPU option (optional)

Ollama uses CPU by default. After installing NVIDIA Container Toolkit and verifying `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi`, add the following under the `ollama` service in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

Do not enable this on hosts without a configured NVIDIA runtime.

## Cloud VPS deployment outline

1. Install Docker Engine + Compose plugin on a supported Linux VPS.
2. Copy the repository securely; create `.env` on the host and set strong unique credentials.
3. Configure a firewall and reverse proxy with HTTPS; do not expose PostgreSQL, Redis, or Ollama publicly.
4. Run `docker compose up --build -d`, pull the model, then verify `/health` and `/ready`.
5. Configure volume backups, log rotation, patching, monitoring, and a recovery procedure before production use.

This is a learning/deployment starter, not a complete internet-facing production platform: add authentication, rate limits, backups, TLS proxy configuration, and secret-manager integration before exposing it publicly.
