import pytest
from task13.vram import estimate_vram

def test_8b_4bit_weights_are_about_4_4gb_with_overhead():
    result = estimate_vram(8, 4, runtime_overhead_gb=1.5)
    assert result.weight_gb == pytest.approx(4.4)
    assert result.total_gb > result.weight_gb

def test_kv_cache_scales_with_concurrency():
    one = estimate_vram(8, 4, concurrency=1)
    four = estimate_vram(8, 4, concurrency=4)
    assert four.kv_cache_gb == pytest.approx(one.kv_cache_gb * 4)

def test_rejects_invalid_precision():
    with pytest.raises(ValueError):
        estimate_vram(8, 3)
