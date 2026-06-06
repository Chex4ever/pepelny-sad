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
    data: bytes | memoryview,
    stride: int,
) -> None:
    """Upload interleaved verts and draw as GL_TRIANGLES without splitting triangles."""
    nbytes = data.nbytes if isinstance(data, memoryview) else len(data)
    data = align_triangle_bytes(
        data.tobytes() if isinstance(data, memoryview) else data, stride
    )
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


def draw_interleaved_from_builder(
    ctx: Any,
    vao: Any,
    vbo: Any,
    vbo_capacity: int,
    ensure_vbo: Callable[[int], None],
    byte_view: memoryview,
    stride: int,
    vertex_count: int,
) -> None:
    """Single upload + draw when vertex count is already triangle-aligned."""
    if vertex_count < 3 or vertex_count % 3 != 0:
        return
    nbytes = vertex_count * stride
    if nbytes <= 0:
        return
    if nbytes <= vbo_capacity:
        ensure_vbo(nbytes)
        vbo.write(byte_view[:nbytes])
        vao.render(mode=ctx.TRIANGLES, vertices=vertex_count)
        return
    data = bytes(byte_view[:nbytes])
    draw_interleaved_triangles(
        ctx, vao, vbo, vbo_capacity, ensure_vbo, data, stride
    )
