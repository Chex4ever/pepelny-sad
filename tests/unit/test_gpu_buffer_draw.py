"""GPU triangle buffer alignment."""
from __future__ import annotations

from src.render.gpu.buffer_draw import align_triangle_bytes, iter_triangle_chunks


def test_align_triangle_bytes_drops_partial_vertex():
    stride = 12
    data = bytes(stride * 5 + 4)
    aligned = align_triangle_bytes(data, stride)
    assert len(aligned) % stride == 0
    assert len(aligned) // stride == 3


def test_iter_triangle_chunks_cover_all_bytes():
    stride = 36
    data = bytes(stride * 100)
    chunks = list(iter_triangle_chunks(data, stride, stride * 40))
    assert chunks
    merged = b"".join(chunks)
    assert merged == align_triangle_bytes(data, stride)
