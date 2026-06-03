"""Per-viewport light grid with radial falloff."""
from __future__ import annotations

import math


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge1 <= edge0:
        return 1.0 if x >= edge1 else 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


class LightMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.values = [[1.0] * width for _ in range(height)]

    def clear(self, ambient: float = 1.0):
        for y in range(self.height):
            row = self.values[y]
            for x in range(self.width):
                row[x] = ambient

    def add_source(self, sx: int, sy: int, radius: float, intensity: float = 0.8):
        if radius <= 0:
            return
        r2 = radius * radius
        y0 = max(0, int(sy - radius - 1))
        y1 = min(self.height, int(sy + radius + 2))
        x0 = max(0, int(sx - radius - 1))
        x1 = min(self.width, int(sx + radius + 2))
        for y in range(y0, y1):
            for x in range(x0, x1):
                dx = x - sx
                dy = y - sy
                d2 = dx * dx + dy * dy
                if d2 > r2:
                    continue
                d = math.sqrt(d2)
                falloff = 1.0 - _smoothstep(radius * 0.2, radius, d)
                self.values[y][x] = min(1.8, self.values[y][x] + intensity * falloff)

    def blur_3x3(self):
        src = [row[:] for row in self.values]
        for y in range(self.height):
            for x in range(self.width):
                total = 0.0
                count = 0
                for dy in (-1, 0, 1):
                    ny = y + dy
                    if ny < 0 or ny >= self.height:
                        continue
                    for dx in (-1, 0, 1):
                        nx = x + dx
                        if nx < 0 or nx >= self.width:
                            continue
                        total += src[ny][nx]
                        count += 1
                self.values[y][x] = total / max(1, count)

    def get(self, x: int, y: int) -> float:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.values[y][x]
        return 1.0

    def apply_to_buffer(self, buffer, ox: int, oy: int):
        """Multiply buffer.light in region by lightmap values."""
        for y in range(self.height):
            for x in range(self.width):
                bx, by = ox + x, oy + y
                if not buffer.in_bounds(bx, by):
                    continue
                i = buffer._idx(bx, by)
                buffer.light[i] = min(1.8, buffer.light[i] * self.values[y][x])
