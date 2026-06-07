"""Diagnostic markers for character editor (air gap, below floor, part gaps)."""
from __future__ import annotations

from dataclasses import dataclass, field

LEG_KINDS = frozenset({"body_leg_l", "body_leg_r"})
FEET_KINDS = LEG_KINDS

# Expected adjacency between body part kinds (8-connectivity within 2 steps).
PART_ADJACENCY: dict[str, frozenset[str]] = {
    "body_torso": frozenset({"body_head", "body_arm_l", "body_arm_r", "body_leg_l", "body_leg_r"}),
    "body_head": frozenset({"body_torso", "hair", "eye", "feature"}),
    "body_arm_l": frozenset({"body_torso"}),
    "body_arm_r": frozenset({"body_torso"}),
    "body_leg_l": frozenset({"body_torso"}),
    "body_leg_r": frozenset({"body_torso"}),
    "hair": frozenset({"body_head"}),
}

AIR_GAP_TILES = 1  # max z gap between feet and floor before 'a'


@dataclass
class DiagnosticMarker:
    x: int
    y: int
    z: int
    glyph: str  # 'a', 'e', 's'
    kind: str = ""


@dataclass
class DiagnosticReport:
    markers: list[DiagnosticMarker] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out = {"a": 0, "e": 0, "s": 0}
        for m in self.markers:
            out[m.glyph] = out.get(m.glyph, 0) + 1
        return out

    def summary(self) -> str:
        c = self.counts()
        if not any(c.values()):
            return "warn: ok"
        parts = [f"{c[k]}×{k}" for k in ("s", "a", "e") if c[k]]
        return "warn: " + " ".join(parts)


def compute_floor_z(
    voxels: dict[tuple[int, int, int], str],
    *,
    default: int = 0,
) -> int:
    leg_z = [z for (_x, _y, z), k in voxels.items() if k in FEET_KINDS]
    if leg_z:
        return min(leg_z)
    if voxels:
        return min(z for (_x, _y, z) in voxels)
    return default


def _neighbors8(x: int, y: int, z: int) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                out.append((x + dx, y + dy, z + dz))
    return out


def _connected_components(
    voxels: dict[tuple[int, int, int], str],
    kind: str,
) -> list[set[tuple[int, int, int]]]:
    positions = {(x, y, z) for (x, y, z), k in voxels.items() if k == kind}
    if not positions:
        return []
    remaining = set(positions)
    components: list[set[tuple[int, int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        comp: set[tuple[int, int, int]] = set()
        stack = [start]
        while stack:
            p = stack.pop()
            if p not in remaining:
                continue
            remaining.discard(p)
            comp.add(p)
            for n in _neighbors8(*p):
                if n in remaining:
                    stack.append(n)
        components.append(comp)
    return components


def _kinds_within_steps(
    voxels: dict[tuple[int, int, int], str],
    start: tuple[int, int, int],
    max_steps: int,
) -> set[str]:
    found: set[str] = set()
    frontier = {start}
    visited = {start}
    for _ in range(max_steps):
        nxt: set[tuple[int, int, int]] = set()
        for p in frontier:
            found.add(voxels[p])
            for n in _neighbors8(*p):
                if n in voxels and n not in visited:
                    visited.add(n)
                    nxt.add(n)
        frontier = nxt
        if not frontier:
            break
    return found


def find_below_floor(
    voxels: dict[tuple[int, int, int], str],
    floor_z: int,
) -> list[DiagnosticMarker]:
    out: list[DiagnosticMarker] = []
    for (x, y, z), kind in voxels.items():
        if z < floor_z:
            out.append(DiagnosticMarker(x, y, z, "e", kind))
    return out


def find_air_gap(
    voxels: dict[tuple[int, int, int], str],
    floor_z: int,
    *,
    walking: bool,
) -> list[DiagnosticMarker]:
    if not walking:
        return []
    foot_z = [z for (_x, _y, z), k in voxels.items() if k in FEET_KINDS]
    if not foot_z:
        return []
    min_feet = min(foot_z)
    if min_feet <= floor_z + AIR_GAP_TILES:
        return []
    # Mark cells between floor and lowest foot in foot columns.
    foot_cols = {(x, y) for (x, y, z), k in voxels.items() if k in FEET_KINDS}
    out: list[DiagnosticMarker] = []
    for x, y in foot_cols:
        for z in range(floor_z, min_feet):
            out.append(DiagnosticMarker(x, y, z, "a"))
    return out


def find_part_gaps(voxels: dict[tuple[int, int, int], str]) -> list[DiagnosticMarker]:
    out: list[DiagnosticMarker] = []
    # Disconnected components within same kind.
    kinds_seen: set[str] = set()
    for (_x, _y, _z), k in voxels.items():
        if k.startswith("body_") or k == "hair":
            kinds_seen.add(k)
    for kind in kinds_seen:
        comps = _connected_components(voxels, kind)
        if len(comps) > 1:
            for comp in comps[1:]:
                cx = sum(p[0] for p in comp) // len(comp)
                cy = sum(p[1] for p in comp) // len(comp)
                cz = sum(p[2] for p in comp) // len(comp)
                out.append(DiagnosticMarker(cx, cy, cz, "s", kind))

    # Missing adjacency between expected part pairs.
    by_kind: dict[str, list[tuple[int, int, int]]] = {}
    for pos, k in voxels.items():
        if k in PART_ADJACENCY or k in {t for v in PART_ADJACENCY.values() for t in v}:
            by_kind.setdefault(k, []).append(pos)

    checked: set[tuple[str, str]] = set()
    for kind_a, neighbors in PART_ADJACENCY.items():
        if kind_a not in by_kind:
            continue
        for kind_b in neighbors:
            if kind_b not in by_kind:
                continue
            pair = tuple(sorted((kind_a, kind_b)))
            if pair in checked:
                continue
            checked.add(pair)
            connected = False
            for pa in by_kind[kind_a]:
                nearby = _kinds_within_steps(voxels, pa, 2)
                if kind_b in nearby:
                    connected = True
                    break
            if not connected:
                pa = by_kind[kind_a][0]
                pb = by_kind[kind_b][0]
                mx = (pa[0] + pb[0]) // 2
                my = (pa[1] + pb[1]) // 2
                mz = (pa[2] + pb[2]) // 2
                out.append(DiagnosticMarker(mx, my, mz, "s", f"{kind_a}-{kind_b}"))
    return out


def analyze_voxels(
    voxels: dict[tuple[int, int, int], str],
    *,
    walking: bool = False,
    floor_z: int | None = None,
) -> DiagnosticReport:
    fz = floor_z if floor_z is not None else compute_floor_z(voxels)
    markers: list[DiagnosticMarker] = []
    markers.extend(find_below_floor(voxels, fz))
    markers.extend(find_air_gap(voxels, fz, walking=walking))
    markers.extend(find_part_gaps(voxels))
    return DiagnosticReport(markers=markers)
