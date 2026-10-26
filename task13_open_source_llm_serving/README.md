# Task 13 — Open-Source LLMs, Quantization & Local Model Serving

A runnable CLI project for testing OpenAI-compatible local model servers, estimating VRAM, and benchmarking concurrent requests.

## Features

- OpenAI-compatible client for Ollama and vLLM (`/v1/models`, `/v1/chat/completions`)
- Single-prompt inference command
- VRAM estimate including model weights, KV cache, and runtime overhead
- Concurrent request benchmark with latency, throughput, token counts, and JSON output
- Unit tests for VRAM calculations
- Optional vLLM Docker deployment example

## 1. Install

Requires Python 3.11+ and `uv`.

```bash
uv sync --extra dev
```

If you don't have `uv`, install it from https://docs.astral.sh/uv/.

## 2. Run with Ollama (recommended for local development)

Install Ollama from https://ollama.com/download, then pull a small model:

```bash
ollama pull qwen2.5:3b
ollama serve
```

Ollama usually listens on port `11434`. In another terminal:

```bash
uv run task13 doctor
uv run task13 chat "Explain 4-bit quantization simply."
uv run task13 benchmark --requests 10 --concurrency 2 --output results/ollama.json
```

The default client base URL is `http://localhost:11434/v1`. Ollama's OpenAI-compatible API accepts an API key field but does not require a real key locally.

Configure a different model or endpoint with environment variables:

```bash
# Git Bash / MINGW
export LLM_BASE_URL="http://localhost:11434/v1"
export LLM_API_KEY="ollama"
export LLM_MODEL="qwen2.5:3b"
uv run task13 doctor
```

For Windows PowerShell, use `$env:LLM_MODEL="qwen2.5:3b"` etc.

## 3. vLLM serving (GPU/Linux recommended)

vLLM generally works best on a supported NVIDIA GPU/Linux environment. Its hardware and CUDA requirements change by version; check the official installation guide before installing.

Example container launch (replace the model with one you are licensed and equipped to run):

```bash
docker run --gpus all --rm -p 8000:8000 \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
  -e HUGGING_FACE_HUB_TOKEN="$HF_TOKEN" \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 --port 8000
```

Then point the project at vLLM:

```bash
export LLM_BASE_URL="http://localhost:8000/v1"
export LLM_API_KEY="EMPTY"
export LLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
uv run task13 doctor
uv run task13 chat "What is PagedAttention?"
uv run task13 benchmark --requests 20 --concurrency 4 --max-tokens 128
```

Do not expose the serving port publicly without authentication and network controls.

## 4. VRAM calculator

```bash
uv run task13 vram --parameters 8 --bits 4 --context 4096 --concurrency 1
uv run task13 vram --parameters 8 --bits 4 --context 8192 --concurrency 4
uv run task13 vram --parameters 8 --bits 8 --context 4096 --concurrency 1
uv run task13 vram --parameters 8 --bits 16 --context 4096 --concurrency 1
```

The calculator uses:

- Weight memory ≈ parameter count × bits per weight ÷ 8
- KV cache ≈ 2 × layers × KV heads × head dimension × bytes per KV value × context tokens × concurrent sequences
- Total ≈ weights + KV cache + runtime overhead

It adds a configurable 10% quantization metadata/packing allowance to the weight estimate by default. The KV-cache estimate assumes every concurrent sequence uses its full context and uses the supplied architecture values. Change `--layers`, `--kv-heads`, and `--head-dim` to better match a model.

This is an engineering estimate, not a guarantee of fit. CUDA graphs, temporary buffers, allocator fragmentation, parallelism, model architecture, and runtime implementation affect actual memory. Quantized weights do not imply a proportionally quantized KV cache.

## 5. Benchmark interpretation

Example:

```bash
uv run task13 benchmark --requests 30 --concurrency 1 --output results/c1.json
uv run task13 benchmark --requests 30 --concurrency 4 --output results/c4.json
uv run task13 benchmark --requests 30 --concurrency 8 --output results/c8.json
```

Compare `throughput_tokens_per_second`, `mean_latency_seconds`, `p95_latency_seconds`, and failures across runs. Keep the model, prompt, output limit, and hardware constant. The client uses API-reported completion tokens when available; if not, it falls back to a rough whitespace count. Reported throughput is aggregate output tokens divided by wall-clock duration, not the average of per-request token rates.

For a fair serving benchmark, repeat runs, warm the model first, and report prompt length, generated token count, concurrency, server version, GPU, and precision. This benchmark does not itself measure GPU utilization or prove a specific speedup.

## 6. Quantization notes

| Format / precision | Typical role                      | Key trade-off                                                      |
| ------------------ | --------------------------------- | ------------------------------------------------------------------ |
| FP16               | High-quality GPU inference        | High weight memory; broad support                                  |
| 8-bit              | Reduced weight memory             | Usually small quality loss; support varies                         |
| 4-bit              | Local/consumer hardware           | Lowest weight memory; quality and speed depend on quantizer/kernel |
| GGUF               | llama.cpp / Ollama ecosystem      | Portable; CPU and hybrid CPU/GPU support                           |
| AWQ / GPTQ         | GPU-focused quantized checkpoints | Kernel, hardware, and runtime compatibility matter                 |

GGUF, AWQ, and GPTQ are not simply interchangeable precision levels: they are formats/quantization approaches with different runtime support. Ollama commonly uses GGUF-based model packaging; vLLM supports selected model formats and quantization methods depending on version and hardware.

## 7. Tests

```bash
uv run pytest
```

## 8. Suggested evaluation checklist

- [ ] `task13 doctor` lists the local model
- [ ] `task13 chat` returns a response
- [ ] Run benchmarks at concurrency 1, 2, 4, and 8
- [ ] Save benchmark JSON reports
- [ ] Compare 4-bit / 8-bit / FP16 only where compatible model variants and hardware are available
- [ ] Run the VRAM calculator at multiple context lengths and concurrency levels
- [ ] Record hardware, server version, model ID, quantization, context, and results in your submission

## Interview concepts

- **Memory-bound decoding:** each generated token requires repeatedly accessing model weights; low arithmetic intensity often makes memory bandwidth a key bottleneck, especially at low batch sizes. At larger batches, compute can become more significant.
- **PagedAttention:** manages KV-cache blocks rather than requiring one contiguous allocation per sequence, improving allocation flexibility and reducing waste.
- **Continuous batching:** admits new requests as sequences finish, improving GPU utilization versus waiting for an entire static batch to complete.
- **Weight vs KV cache:** weight quantization reduces model-weight memory, while KV-cache memory scales with sequence length and active sequences and may remain in FP16/BF16.
