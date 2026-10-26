from dataclasses import dataclass

@dataclass(frozen=True)
class VramEstimate:
    weight_gb: float
    kv_cache_gb: float
    runtime_overhead_gb: float
    total_gb: float

def estimate_vram(
    parameters_billions: float,
    bits_per_weight: int = 4,
    context_tokens: int = 4096,
    concurrent_requests: int = 1,
    layers: int = 32,
    kv_heads: int = 8,
    head_dim: int = 128,
    kv_bytes: int = 2,
    runtime_overhead_gb: float = 1.5,
    quantization_overhead_fraction: float = 0.10,
) -> VramEstimate:
    """Approximate VRAM; KV cache assumes GQA-style KV heads and uniform full context."""
    if parameters_billions <= 0:
        raise ValueError("parameters_billions must be positive")
    if bits_per_weight not in (4, 8, 16):
        raise ValueError("bits_per_weight must be one of 4, 8, or 16")
    if min(context_tokens, concurrent_requests, layers, kv_heads, head_dim, kv_bytes) <= 0:
        raise ValueError("context and model dimensions must be positive")
    raw_weights = parameters_billions * 1e9 * bits_per_weight / 8 / 1e9
    weights = raw_weights * (1 + quantization_overhead_fraction)
    # K and V, per token, layer, KV head, head dimension, and concurrent sequence.
    kv = (2 * layers * kv_heads * head_dim * kv_bytes * context_tokens
          * concurrent_requests) / 1e9
    total = weights + kv + runtime_overhead_gb
    return VramEstimate(weights, kv, runtime_overhead_gb, total)
