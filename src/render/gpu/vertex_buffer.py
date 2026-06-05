"""Fast CPU-side vertex accumulation for moderngl uploads."""
from __future__ import annotations

from array import array


class FloatBufferBuilder:
    """Growable float buffer; tobytes() for VBO.write without struct.pack(*huge)."""

    __slots__ = ("_data",)

    def __init__(self) -> None:
        self._data = array("f")

    def clear(self) -> None:
        self._data = array("f")

    def __len__(self) -> int:
        return len(self._data)

    def vertex_count(self) -> int:
        return len(self._data) // 9

    def vertex_count_ui(self) -> int:
        return len(self._data) // 20

    def append_quad_9(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        u0: float,
        v0: float,
        u1: float,
        v1: float,
        r: float,
        g: float,
        b: float,
        a: float,
        fog: float,
    ) -> None:
        d = self._data
        ext = d.extend
        for idx in (0, 1, 2, 0, 2, 3):
            px, py = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))[idx]
            ext((px, py, r, g, b, a, fog, x0, y0, x1, y1, u0, v0, u1, v1))

    def append_quad_12(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        u0: float,
        v0: float,
        u1: float,
        v1: float,
        fr: float,
        fg: float,
        fb: float,
        br: float,
        bg: float,
        bb: float,
        ba: float,
        light: float,
        fog: float,
        fg_a: float = 1.0,
    ) -> None:
        """Axis-aligned quad; UV sampled from v_pos in shader (avoids tri diagonal)."""
        d = self._data
        ext = d.extend
        # TL-BR diagonal split (not TR-BL) + per-quad bounds for fragment UV
        tris = (0, 1, 2, 0, 2, 3)
        corners_xy = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
        for idx in tris:
            px, py = corners_xy[idx]
            ext(
                (
                    px,
                    py,
                    fr,
                    fg,
                    fb,
                    br,
                    bg,
                    bb,
                    ba,
                    light,
                    fog,
                    fg_a,
                    x0,
                    y0,
                    x1,
                    y1,
                    u0,
                    v0,
                    u1,
                    v1,
                )
            )

    def tobytes(self) -> bytes:
        return self._data.tobytes()
