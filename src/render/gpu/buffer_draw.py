"""Safe VBO upload for interleaved triangle lists (moderngl)."""
from __future__ import annotations

from typing import Any, Callable


def align_triangle_bytes(data: bytes, stride: int) -> bytes:
    """Trim trailing bytes and drop 1–2 verts so count is a multiple of 3."""
    if stride <= 0 or not data:
        return b""
    vert_bytes = (len(data) // stride) * stride
    data = data[:vert_bytes]
    verts = vert_bytes // stride
    verts -= verts % 3
    return data[: verts * stride]


def iter_triangle_chunks(data: bytes, stride: int, max_bytes: int):
    """Yield triangle-list chunks aligned to vertex and triangle boundaries."""
    data = align_triangle_bytes(data, stride)
    if not data:
        return
    max_bytes = max(stride * 3, (max_bytes // stride) // 3 * 3 * stride)
    offset = 0
    while offset < len(data):
        end = min(offset + max_bytes, len(data))
        chunk = data[offset:end]
        chunk = align_triangle_bytes(chunk, stride)
        if len(chunk) >= stride * 3:
            yield chunk
        offset += len(chunk)


def draw_interleaved_triangles(
    ctx: Any,
    vao: Any,
    vbo: Any,
    vbo_capacity: int,
    ensure_vbo: Callable[[int], None],
    data: bytes,
    stride: int,
) -> None:
    """Upload interleaved verts and draw as GL_TRIANGLES without splitting triangles."""
    data = align_triangle_bytes(data, stride)
    if not data:
        return
    if len(data) <= vbo_capacity:
        ensure_vbo(len(data))
        vbo.write(data)
        vao.render(mode=ctx.TRIANGLES, vertices=len(data) // stride)
        return
    for chunk in iter_triangle_chunks(data, stride, vbo_capacity):
        ensure_vbo(len(chunk))
        vbo.write(chunk)
        vao.render(mode=ctx.TRIANGLES, vertices=len(chunk) // stride)
