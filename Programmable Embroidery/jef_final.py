"""
jef_final.py

Final JEF (Janome Embroidery Format) generator for MECE4606.

Features for rubric:
- Generates JEF files directly (no external libs).
- Patterns that fit in 10x10 cm: circle, rectangle, star.
- Parametric fractal (Koch snowflake) – NOT a tree.
- Optional fractal tree (second fractal type).
- User-specified text using a simple vector stroke font.
- Multiple thread colors and color changes in a single design.
- Many user parameters in an interactive text interface.

All distances are in millimeters. 1 stitch unit = 0.1 mm.
"""

import math
import struct
from datetime import datetime
from math import cos, sin, pi, sqrt, ceil
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# ------------------------ JEF constants & utilities ------------------------

JEF_COLOR_CODES: Dict[str, int] = {
    "black": 1,
    "white": 2,
    "red": 10,
    "blue": 12,
    "green": 6,
    "yellow": 48,
    "pink": 9,
    "gold": 13,
}

HOOP_SIZES = {
    0: (126, 110),   # A Standard
    1: (50, 50),     # C Free Arm
    2: (140, 200),   # B Large
    3: (126, 110),   # F Spring Loaded
    4: (230, 200),   # D Giga
}

MAX_STITCH_DELTA = 127  # max displacement per stitch/jump byte
CMD_ESCAPE = 0x80
CMD_COLOR_CHANGE = 0x01
CMD_JUMP_TRIM = 0x02
CMD_END = 0x10


def write_jef_header(
    f,
    stitch_offset: int,
    color_count: int,
    stitch_count: int,
    hoop_code: int,
    extents_01mm: Tuple[int, int, int, int],
) -> None:
    """Write JEF file header (116 bytes)."""
    f.write(struct.pack("<I", stitch_offset))
    f.write(struct.pack("<I", 0x14))
    f.write(datetime.now().strftime("%Y%m%d").encode("ascii").ljust(8)[:8])
    f.write(datetime.now().strftime("%H%M%S00").encode("ascii").ljust(8)[:8])
    f.write(struct.pack("<I", color_count))
    f.write(struct.pack("<I", stitch_count))
    f.write(struct.pack("<I", hoop_code))
    l, t, r, b = extents_01mm
    f.write(struct.pack("<iiii", l, t, r, b))
    for _ in range(4):
        f.write(struct.pack("<iiii", -1, -1, -1, -1))


def write_thread_tables(f, color_codes: List[int]) -> None:
    for code in color_codes:
        f.write(struct.pack("<I", code))
    for _ in color_codes:
        f.write(struct.pack("<I", 0x0D))


def count_stitches(stitch_bytes: bytes) -> int:
    n = 0
    i = 0
    while i < len(stitch_bytes):
        b = stitch_bytes[i]
        if b == CMD_ESCAPE:
            cmd = stitch_bytes[i + 1]
            if cmd == CMD_END:
                break
            if cmd == CMD_JUMP_TRIM:
                i += 4
            else:
                i += 2
        else:
            i += 2
            n += 1
    return n


# -------------------- Stitch encoder (integer-unit tracking) --------------------


def _emit_jump_sequence(out: bytearray, dx: int, dy: int) -> None:
    """Emit one or more JUMP commands to cover (dx, dy) in integer 0.1-mm units.

    When the displacement exceeds 127 units in either axis, multiple
    JUMP commands are chained so the needle actually reaches the target.
    """
    while dx != 0 or dy != 0:
        jx = max(-MAX_STITCH_DELTA, min(MAX_STITCH_DELTA, dx))
        jy = max(-MAX_STITCH_DELTA, min(MAX_STITCH_DELTA, dy))
        out.extend(bytes([CMD_ESCAPE, CMD_JUMP_TRIM]))
        out.extend(struct.pack("<bb", jx, jy))
        dx -= jx
        dy -= jy


def points_sequences_to_stitches(
    sequences: List[List],
    units_per_mm: float = 10.0,
    use_color_changes: bool = True,
) -> bytes:
    """
    Convert multiple sequences of absolute (x, y) points in mm into JEF stitch bytes.

    - Inserts COLOR_CHANGE between sequences when use_color_changes is True.
    - Handles large displacements by emitting multiple JUMP commands.
    - None entries inside a sequence indicate a jump (pen-up) to the next point.
    - Tracks needle position in integer units (0.1 mm) to prevent cumulative drift.
    """
    out = bytearray()
    needle_x, needle_y = 0, 0  # integer units (0.1 mm)

    first_seq = True
    for seq in sequences:
        if not seq:
            continue

        if not first_seq and use_color_changes:
            out.append(CMD_ESCAPE)
            out.append(CMD_COLOR_CHANGE)
        first_seq = False

        need_jump = False
        for p in seq:
            if p is None:
                need_jump = True
                continue

            x, y = p
            target_x = int(round(x * units_per_mm))
            target_y = int(round(y * units_per_mm))
            dx = target_x - needle_x
            dy = target_y - needle_y

            if need_jump or abs(dx) > MAX_STITCH_DELTA or abs(dy) > MAX_STITCH_DELTA:
                _emit_jump_sequence(out, dx, dy)
                needle_x = target_x
                needle_y = target_y
                need_jump = False
            else:
                out.extend(struct.pack("<bb", dx, dy))
                needle_x += dx
                needle_y += dy

    out.append(CMD_ESCAPE)
    out.append(CMD_END)
    return bytes(out)


def compute_extents_01mm(sequences: List[List]) -> Tuple[int, int, int, int]:
    """Compute design extents (left, top, right, bottom) in 0.1 mm."""
    xs: List[float] = []
    ys: List[float] = []
    for seq in sequences:
        for p in seq:
            if p is None:
                continue
            xs.append(p[0])
            ys.append(p[1])
    if not xs or not ys:
        return (0, 0, 0, 0)
    return (
        int(round(min(xs) * 10)),
        int(round(min(ys) * 10)),
        int(round(max(xs) * 10)),
        int(round(max(ys) * 10)),
    )


def write_jef_multi(
    path,
    sequences: List[List],
    color_names: List[str],
    hoop_code: int = 0,
) -> None:
    """Write a complete JEF file with multiple color sequences."""
    if not sequences:
        raise ValueError("No sequences to write.")

    color_codes = [JEF_COLOR_CODES.get(n.lower(), 1) for n in color_names]
    color_count = max(1, min(len(color_codes), len(sequences)))
    stitch_bytes = points_sequences_to_stitches(sequences[:color_count])
    stitch_count = count_stitches(stitch_bytes)
    stitch_offset = 116 + 8 * color_count
    extents_01mm = compute_extents_01mm(sequences[:color_count])

    path = Path(path)
    if path.suffix.lower() != ".jef":
        path = path.with_suffix(".jef")

    with path.open("wb") as f:
        write_jef_header(f, stitch_offset, color_count, stitch_count,
                         hoop_code, extents_01mm)
        write_thread_tables(f, color_codes[:color_count])
        f.write(stitch_bytes)


# ------------------------ Geometry: basic patterns ------------------------


def circle_points(cx: float, cy: float, radius: float,
                  spacing: float = 0.8) -> List[Tuple[float, float]]:
    n = max(16, int(ceil(2 * pi * radius / spacing)))
    return [(cx + radius * cos(2 * pi * i / n),
             cy + radius * sin(2 * pi * i / n)) for i in range(n + 1)]


def circle_fill_points(cx: float, cy: float, radius: float,
                       spacing: float = 0.8) -> List:
    """Concentric circle fill from center outward."""
    pts: List = []
    n_rings = max(1, int(radius / spacing))
    for ring in range(n_rings, 0, -1):
        r = radius * ring / n_rings
        n = max(8, int(ceil(2 * pi * r / spacing)))
        ring_pts = [(cx + r * cos(2 * pi * i / n),
                     cy + r * sin(2 * pi * i / n)) for i in range(n + 1)]
        if pts:
            pts.append(None)
        pts.extend(ring_pts)
    return pts


def rectangle_points(left: float, top: float, w: float, h: float,
                     spacing: float = 0.8) -> List[Tuple[float, float]]:
    r, b = left + w, top + h
    pts: List[Tuple[float, float]] = []
    nt = max(1, int(ceil(w / spacing)))
    for i in range(nt + 1):
        pts.append((left + w * i / nt, top))
    nr = max(1, int(ceil(h / spacing)))
    for i in range(1, nr + 1):
        pts.append((r, top + h * i / nr))
    nb = max(1, int(ceil(w / spacing)))
    for i in range(1, nb + 1):
        pts.append((r - w * i / nb, b))
    nl = max(1, int(ceil(h / spacing)))
    for i in range(1, nl):
        pts.append((left, b - h * i / nl))
    pts.append((left, top))
    return pts


def rectangle_fill_points(left: float, top: float, w: float, h: float,
                           spacing: float = 0.8) -> List:
    """Horizontal row fill (hatching)."""
    pts: List = []
    r, b = left + w, top + h
    n_rows = max(1, int(h / spacing))
    for i in range(n_rows):
        y = top + (i + 0.5) * h / n_rows
        n_cols = max(1, int(w / spacing))
        if i % 2 == 0:
            row_pts = [(left + w * j / n_cols, y) for j in range(n_cols + 1)]
        else:
            row_pts = [(left + w * (n_cols - j) / n_cols, y) for j in range(n_cols + 1)]
        if pts:
            pts.append(None)
        pts.extend(row_pts)
    return pts


def star_points(cx: float, cy: float, outer_r: float, inner_r: float,
                num_pts: int = 5, spacing: float = 0.8) -> List[Tuple[float, float]]:
    """
    Star outline with subdivided segments (avoids empty/degenerate paths that
    trigger Ink/Stitch bounding box errors).
    """
    if num_pts < 2:
        num_pts = 5
    vertices: List[Tuple[float, float]] = []
    for i in range(num_pts * 2):
        r = outer_r if i % 2 == 0 else inner_r
        t = pi * i / num_pts - pi / 2
        vertices.append((cx + r * cos(t), cy + r * sin(t)))
    vertices.append(vertices[0])
    pts: List[Tuple[float, float]] = [vertices[0]]
    for i in range(len(vertices) - 1):
        x0, y0 = vertices[i]
        x1, y1 = vertices[i + 1]
        seg_len = sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
        n = max(1, int(ceil(seg_len / spacing)))
        for j in range(1, n + 1):
            t = j / n
            pts.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
    return pts


def star_fill_points(cx: float, cy: float, outer_r: float, inner_r: float,
                     num_pts: int = 5, spacing: float = 0.8) -> List:
    """Concentric inset star fill."""
    if num_pts < 2:
        num_pts = 5
    n_rings = max(1, int(outer_r / spacing))
    pts: List = []
    for ring in range(n_rings, 0, -1):
        scale = ring / n_rings
        vertices: List[Tuple[float, float]] = []
        for i in range(num_pts * 2):
            r = (outer_r if i % 2 == 0 else inner_r) * scale
            t = pi * i / num_pts - pi / 2
            vertices.append((cx + r * cos(t), cy + r * sin(t)))
        vertices.append(vertices[0])
        ring_pts: List[Tuple[float, float]] = [vertices[0]]
        for i in range(len(vertices) - 1):
            x0, y0 = vertices[i]
            x1, y1 = vertices[i + 1]
            seg_len = sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            n = max(1, int(ceil(seg_len / spacing)))
            for j in range(1, n + 1):
                t = j / n
                ring_pts.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
        if pts:
            pts.append(None)
        pts.extend(ring_pts)
    return pts


# ----------------------- Fractals (corrected formulas) -----------------------


def _koch_segment(p0: Tuple[float, float], p1: Tuple[float, float],
                  depth: int, pts: List[Tuple[float, float]]) -> None:
    """
    Recursively subdivide segment p0->p1 into Koch curve and append to pts.

    At depth 0 just appends p1.  Otherwise splits into 4 sub-segments:
        p0 -> A -> C -> B -> p1

    where A = p0 + (p1-p0)/3, B = p0 + 2(p1-p0)/3, and C is the peak
    of an equilateral triangle on segment A-B:

        C = A + rotate(B - A, +60 degrees)
        rotate((x,y), 60) = (x*cos60 - y*sin60, x*sin60 + y*cos60)
    """
    if depth == 0:
        pts.append(p1)
        return

    x0, y0 = p0
    x1, y1 = p1
    dx3 = (x1 - x0) / 3.0
    dy3 = (y1 - y0) / 3.0

    pA = (x0 + dx3, y0 + dy3)
    pB = (x0 + 2.0 * dx3, y0 + 2.0 * dy3)

    cos60 = 0.5
    sin60 = sqrt(3.0) / 2.0
    pC = (pA[0] + dx3 * cos60 - dy3 * sin60,
          pA[1] + dx3 * sin60 + dy3 * cos60)

    _koch_segment(p0, pA, depth - 1, pts)
    _koch_segment(pA, pC, depth - 1, pts)
    _koch_segment(pC, pB, depth - 1, pts)
    _koch_segment(pB, p1, depth - 1, pts)


def koch_snowflake_points(cx: float, cy: float, side: float,
                          depth: int) -> List[Tuple[float, float]]:
    """
    Koch snowflake: start with equilateral triangle, apply Koch subdivision
    to each edge.  depth 0 = plain triangle, 1-4 = increasingly detailed.
    """
    depth = max(0, min(depth, 4))
    h = side * sqrt(3.0) / 2.0

    # Equilateral triangle centred at (cx, cy), point at top (negative Y).
    # Traversed clockwise so Koch bumps point outward.
    v_top   = (cx,              cy - 2.0 * h / 3.0)
    v_left  = (cx - side / 2.0, cy + h / 3.0)
    v_right = (cx + side / 2.0, cy + h / 3.0)

    pts: List[Tuple[float, float]] = [v_top]
    _koch_segment(v_top, v_right, depth, pts)
    _koch_segment(v_right, v_left, depth, pts)
    _koch_segment(v_left, v_top, depth, pts)
    return pts


def _subdivide_path(path: List[Tuple[float, float]], max_seg_mm: float) -> List[Tuple[float, float]]:
    """Subdivide path segments longer than max_seg_mm."""
    if len(path) < 2 or max_seg_mm <= 0:
        return path
    out: List[Tuple[float, float]] = [path[0]]
    for i in range(1, len(path)):
        x0, y0 = path[i - 1]
        x1, y1 = path[i]
        dx, dy = x1 - x0, y1 - y0
        length = sqrt(dx * dx + dy * dy)
        n = max(1, int(ceil(length / max_seg_mm)))
        for j in range(1, n + 1):
            t = j / n
            out.append((x0 + t * dx, y0 + t * dy))
    return out


def koch_snowflake_fill_points(cx: float, cy: float, side: float,
                               depth: int, spacing: float = 0.8) -> List:
    """Concentric Koch snowflake fill."""
    depth = max(0, min(depth, 4))
    h = side * sqrt(3.0) / 2.0
    radius_approx = 2.0 * h / 3.0
    n_rings = max(1, int(radius_approx / spacing))
    pts: List = []
    for ring in range(n_rings, 0, -1):
        scale = ring / n_rings
        side_i = side * scale
        h_i = side_i * sqrt(3.0) / 2.0
        v_top = (cx, cy - 2.0 * h_i / 3.0)
        v_left = (cx - side_i / 2.0, cy + h_i / 3.0)
        v_right = (cx + side_i / 2.0, cy + h_i / 3.0)
        ring_pts: List[Tuple[float, float]] = [v_top]
        _koch_segment(v_top, v_right, depth, ring_pts)
        _koch_segment(v_right, v_left, depth, ring_pts)
        _koch_segment(v_left, v_top, depth, ring_pts)
        ring_pts = _subdivide_path(ring_pts, spacing)
        if pts:
            pts.append(None)
        pts.extend(ring_pts)
    return pts


def fractal_tree_points(
    base_x: float, base_y: float,
    length: float, angle_rad: float,
    depth: int, angle_delta: float, scale: float,
) -> List[Tuple[float, float]]:
    """Simple recursive fractal tree (backtracking produces over-stitching on trunk)."""
    pts: List[Tuple[float, float]] = [(base_x, base_y)]

    def _rec(x, y, ln, ang, d):
        if d == 0 or ln < 1.0:
            return
        x2 = x + ln * cos(ang)
        y2 = y + ln * sin(ang)
        pts.append((x2, y2))
        _rec(x2, y2, ln * scale, ang + angle_delta, d - 1)
        pts.append((x2, y2))
        _rec(x2, y2, ln * scale, ang - angle_delta, d - 1)
        pts.append((x, y))

    _rec(base_x, base_y, length, angle_rad, depth)
    return pts


# -------------------- Simple stroke font for text --------------------

# Each character is a list of strokes.  Each stroke is a list of (x, y)
# in a normalised [0,1] x [0,1] cell where (0,0)=bottom-left, (1,1)=top-right.

FONT_STROKES: Dict[str, List[List[Tuple[float, float]]]] = {}


def _add(ch: str, strokes: List[List[Tuple[float, float]]]):
    FONT_STROKES[ch] = strokes


# --- Uppercase letters (block style, continuous strokes) ---
_add("A", [[(0, 0), (0, 1)], [(0, 1), (1, 1)], [(1, 1), (1, 0)], [(0, 0.5), (1, 0.5)]])
_add("B", [[(0, 0), (0, 1), (0.7, 1), (0.8, 0.9), (0.8, 0.6), (0.7, 0.5),
            (0, 0.5), (0.7, 0.5), (0.8, 0.4), (0.8, 0.1), (0.7, 0), (0, 0)]])
_add("C", [[(1, 1), (0.3, 1), (0, 0.7), (0, 0.3), (0.3, 0), (1, 0)]])
_add("D", [[(0, 0), (0, 1), (0.6, 1), (1, 0.7), (1, 0.3), (0.6, 0), (0, 0)]])
_add("E", [[(1, 1), (0, 1), (0, 0), (1, 0)], [(0, 0.5), (0.7, 0.5)]])
_add("F", [[(0, 0), (0, 1), (1, 1)], [(0, 0.5), (0.7, 0.5)]])
_add("G", [[(1, 1), (0.3, 1), (0, 0.7), (0, 0.3), (0.3, 0),
            (1, 0), (1, 0.5), (0.5, 0.5)]])
_add("H", [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, 0.5), (1, 0.5)]])
_add("I", [[(0.2, 1), (0.8, 1)], [(0.5, 1), (0.5, 0)], [(0.2, 0), (0.8, 0)]])
_add("J", [[(0.2, 1), (0.8, 1)], [(0.5, 1), (0.5, 0.2), (0.3, 0), (0.1, 0.2)]])
_add("K", [[(0, 0), (0, 1)], [(1, 1), (0, 0.5), (1, 0)]])
_add("L", [[(0, 1), (0, 0), (1, 0)]])
_add("M", [[(0, 0), (0, 1), (0.5, 0.5), (1, 1), (1, 0)]])
_add("N", [[(0, 0), (0, 1), (1, 0), (1, 1)]])
_add("O", [[(0, 0.3), (0, 0.7), (0.3, 1), (0.7, 1), (1, 0.7),
            (1, 0.3), (0.7, 0), (0.3, 0), (0, 0.3)]])
_add("P", [[(0, 0), (0, 1), (0.7, 1), (1, 0.8), (0.7, 0.5), (0, 0.5)]])
_add("Q", [[(0, 0.3), (0, 0.7), (0.3, 1), (0.7, 1), (1, 0.7),
            (1, 0.3), (0.7, 0), (0.3, 0), (0, 0.3)], [(0.6, 0.2), (1.0, -0.1)]])
_add("R", [[(0, 0), (0, 1), (0.7, 1), (1, 0.8), (0.7, 0.5), (0, 0.5)],
           [(0.5, 0.5), (1, 0)]])
_add("S", [[(1, 1), (0.3, 1), (0, 0.8), (0.3, 0.5), (0.7, 0.5),
            (1, 0.2), (0.7, 0), (0, 0)]])
_add("T", [[(0, 1), (1, 1)], [(0.5, 1), (0.5, 0)]])
_add("U", [[(0, 1), (0, 0.3), (0.3, 0), (0.7, 0), (1, 0.3), (1, 1)]])
_add("V", [[(0, 1), (0.5, 0), (1, 1)]])
_add("W", [[(0, 1), (0.2, 0), (0.5, 0.6), (0.8, 0), (1, 1)]])
_add("X", [[(0, 1), (1, 0)], [(0, 0), (1, 1)]])
_add("Y", [[(0, 1), (0.5, 0.5), (1, 1)], [(0.5, 0.5), (0.5, 0)]])
_add("Z", [[(0, 1), (1, 1), (0, 0), (1, 0)]])

# --- Digits ---
_add("0", [[(0, 0.3), (0, 0.7), (0.3, 1), (0.7, 1), (1, 0.7),
            (1, 0.3), (0.7, 0), (0.3, 0), (0, 0.3)]])
_add("1", [[(0.3, 0.8), (0.5, 1), (0.5, 0)], [(0.2, 0), (0.8, 0)]])
_add("2", [[(0, 0.8), (0.3, 1), (0.7, 1), (1, 0.8), (0, 0), (1, 0)]])
_add("3", [[(0, 0.8), (0.3, 1), (0.7, 1), (1, 0.8), (0.7, 0.5),
            (0.3, 0.5), (0.7, 0.5), (1, 0.2), (0.7, 0), (0.3, 0), (0, 0.2)]])
_add("4", [[(0, 1), (0, 0.5), (1, 0.5)], [(0.8, 1), (0.8, 0)]])
_add("5", [[(1, 1), (0, 1), (0, 0.5), (0.7, 0.5), (1, 0.3), (0.7, 0), (0, 0)]])
_add("6", [[(0.7, 1), (0.3, 1), (0, 0.7), (0, 0.3), (0.3, 0), (0.7, 0),
            (1, 0.3), (0.7, 0.5), (0, 0.5)]])
_add("7", [[(0, 1), (1, 1), (0.4, 0)]])
_add("8", [[(0.3, 0.5), (0, 0.3), (0.3, 0), (0.7, 0), (1, 0.3), (0.7, 0.5),
            (0.3, 0.5), (0, 0.7), (0.3, 1), (0.7, 1), (1, 0.7), (0.7, 0.5)]])
_add("9", [[(0.3, 0), (0.7, 0), (1, 0.3), (1, 0.7), (0.7, 1), (0.3, 1),
            (0, 0.7), (0.3, 0.5), (1, 0.5)]])
_add(".", [[(0.4, 0), (0.6, 0), (0.6, 0.1), (0.4, 0.1), (0.4, 0)]])
_add("-", [[(0.2, 0.5), (0.8, 0.5)]])
_add("!", [[(0.5, 1), (0.5, 0.3)], [(0.5, 0.1), (0.5, 0)]])


def _subdivide_segment(
    x0: float, y0: float, x1: float, y1: float,
    max_segment_mm: float,
) -> List[Tuple[float, float]]:
    """Subdivide segment (x0,y0)->(x1,y1) so no sub-segment exceeds max_segment_mm."""
    dx = x1 - x0
    dy = y1 - y0
    length = sqrt(dx * dx + dy * dy)
    if length <= max_segment_mm or max_segment_mm <= 0:
        return [(x1, y1)]
    n = max(1, int(ceil(length / max_segment_mm)))
    pts: List[Tuple[float, float]] = []
    for i in range(1, n + 1):
        t = i / n
        pts.append((x0 + t * dx, y0 + t * dy))
    return pts


def text_to_points(
    text: str,
    start_x_mm: float,
    baseline_y_mm: float,
    height_mm: float,
    letter_spacing: float = 0.3,
    spacing_mm: float = 0.8,
) -> List:
    """
    Convert text to stitch points in mm.

    Font cell: (0,0)=bottom-left, (1,1)=top-right.

    JEF uses a Cartesian Y-up coordinate system (larger Y = above baseline).
    We map font y=0 (bottom) to baseline_y_mm and font y=1 (top) to
    baseline_y_mm + height_mm so the text appears right-side-up.

    None sentinels separate strokes so the stitch encoder inserts JUMP
    commands instead of drawing connecting lines between strokes.

    spacing_mm subdivides long segments so no stitch exceeds that length
    (avoids broken/pulled stitches from overly long segments).
    """
    pts: List = []
    text = text.upper()
    x_cursor = start_x_mm
    char_w = height_mm * 0.7

    for ch in text:
        if ch == " ":
            x_cursor += char_w * (1.0 + letter_spacing)
            continue

        strokes = FONT_STROKES.get(ch)
        if not strokes:
            x_cursor += char_w * (1.0 + letter_spacing)
            continue

        for stroke in strokes:
            if not stroke:
                continue
            if pts:
                pts.append(None)
            prev_x = x_cursor + stroke[0][0] * char_w
            prev_y = baseline_y_mm + stroke[0][1] * height_mm
            pts.append((prev_x, prev_y))
            for sx, sy in stroke[1:]:
                x = x_cursor + sx * char_w
                y = baseline_y_mm + sy * height_mm
                for px, py in _subdivide_segment(prev_x, prev_y, x, y, spacing_mm):
                    pts.append((px, py))
                prev_x, prev_y = x, y

        x_cursor += char_w * (1.0 + letter_spacing)

    return pts


# ------------------------ Interactive interface ------------------------


def prompt_float(prompt: str, default: float) -> float:
    s = input(f"{prompt} [{default}]: ").strip()
    return float(s) if s else default


def prompt_int(prompt: str, default: int) -> int:
    s = input(f"{prompt} [{default}]: ").strip()
    return int(s) if s else default


def prompt_color(prompt: str, default: str = "black") -> str:
    s = input(f"{prompt} [{default}]: ").strip().lower()
    if not s:
        s = default
    if s not in JEF_COLOR_CODES:
        print(f"Unknown color '{s}', using '{default}'.")
        s = default
    return s


def prompt_fill(prompt: str = "Fill shape (y/n)", default: bool = False) -> bool:
    s = input(f"{prompt} [{'y' if default else 'n'}]: ").strip().lower()
    if not s:
        return default
    return s in ("y", "yes", "1")


def main():
    print("=== JEF Embroidery File Generator (Final) ===")
    print("All sizes are in millimeters. Keep your design within 100 x 100 mm.")
    print("Available colors:", ", ".join(JEF_COLOR_CODES.keys()))
    print()
    print("Patterns:")
    print("  1) Circle")
    print("  2) Rectangle")
    print("  3) Star")
    print("  4) Koch snowflake (fractal, NOT a tree)")
    print("  5) Fractal tree")
    print("  6) Text")
    print("  7) Koch snowflake + text (two colors)")
    print()

    output_name = input("Output file name [design.jef]: ").strip() or "design.jef"

    hoop_code = prompt_int("Hoop code (0=126x110, 1=50x50, 2=140x200, 3=126x110 spring, 4=230x200)", 0)
    hoop_code = max(0, min(4, hoop_code))
    spacing_mm = prompt_float("Approximate stitch spacing (mm)", 0.8)

    sequences: List[List] = []
    colors: List[str] = []

    while True:
        choice_str = input("\nSelect pattern to ADD (1-7), or 0 to finish: ").strip()
        if choice_str == "" or choice_str == "0":
            break
        try:
            pc = int(choice_str)
        except ValueError:
            print("Please enter 0-7.")
            continue
        if not (1 <= pc <= 7):
            print("Please enter 0-7.")
            continue

        if pc == 1:
            print("\n-- Circle --")
            cx = prompt_float("Center X", 0.0)
            cy = prompt_float("Center Y", 0.0)
            radius = prompt_float("Radius (<= 50 mm)", 20.0)
            fill = prompt_fill()
            color = prompt_color("Thread color", "blue")
            seq = circle_fill_points(cx, cy, radius, spacing_mm) if fill else circle_points(cx, cy, radius, spacing_mm)
            sequences.append(seq)
            colors.append(color)

        elif pc == 2:
            print("\n-- Rectangle --")
            lf = prompt_float("Left X", -20.0)
            tp = prompt_float("Top Y", -20.0)
            w = prompt_float("Width", 40.0)
            h = prompt_float("Height", 40.0)
            fill = prompt_fill()
            color = prompt_color("Thread color", "green")
            seq = rectangle_fill_points(lf, tp, w, h, spacing_mm) if fill else rectangle_points(lf, tp, w, h, spacing_mm)
            sequences.append(seq)
            colors.append(color)

        elif pc == 3:
            print("\n-- Star --")
            cx = prompt_float("Center X", 0.0)
            cy = prompt_float("Center Y", 0.0)
            outer = prompt_float("Outer radius", 30.0)
            inner = prompt_float("Inner radius", 12.0)
            npts = prompt_int("Number of points", 5)
            fill = prompt_fill()
            color = prompt_color("Thread color", "gold")
            seq = star_fill_points(cx, cy, outer, inner, npts, spacing_mm) if fill else star_points(cx, cy, outer, inner, npts, spacing_mm)
            sequences.append(seq)
            colors.append(color)

        elif pc == 4:
            print("\n-- Koch Snowflake (Fractal, NOT a tree) --")
            cx = prompt_float("Center X", 0.0)
            cy = prompt_float("Center Y", 0.0)
            side = prompt_float("Triangle side length (<= 60 mm)", 50.0)
            depth = prompt_int("Recursion depth (0-4)", 3)
            fill = prompt_fill()
            color = prompt_color("Thread color", "red")
            seq = koch_snowflake_fill_points(cx, cy, side, depth, spacing_mm) if fill else koch_snowflake_points(cx, cy, side, depth)
            sequences.append(seq)
            colors.append(color)

        elif pc == 5:
            print("\n-- Fractal Tree --")
            bx = prompt_float("Base X", 0.0)
            by = prompt_float("Base Y", 40.0)
            length = prompt_float("Initial trunk length", 30.0)
            depth = prompt_int("Recursion depth (2-6)", 4)
            ang = prompt_float("Branch angle (degrees)", 30.0)
            sc = prompt_float("Length scale per level (0.4-0.8)", 0.65)
            color = prompt_color("Thread color", "green")
            sequences.append(fractal_tree_points(
                bx, by, length, -pi / 2.0, depth, ang * pi / 180.0, sc))
            colors.append(color)

        elif pc == 6:
            print("\n-- Text --")
            text = input("Text to embroider (A-Z, 0-9, space): ").strip() or "MECE4606"
            sx = prompt_float("Start X", -40.0)
            by = prompt_float("Baseline Y (bottom of text)", 0.0)
            ht = prompt_float("Character height", 15.0)
            color = prompt_color("Thread color", "black")
            sequences.append(text_to_points(text, sx, by, ht, spacing_mm=spacing_mm))
            colors.append(color)

        elif pc == 7:
            print("\n-- Koch Snowflake + Text (Two Colors) --")
            cx = prompt_float("Snowflake center X", 0.0)
            cy = prompt_float("Snowflake center Y", -5.0)
            side = prompt_float("Snowflake side length (<= 60 mm)", 40.0)
            depth = prompt_int("Snowflake recursion depth (0-4)", 3)
            fill = prompt_fill()
            cf = prompt_color("Snowflake color", "blue")
            seq = koch_snowflake_fill_points(cx, cy, side, depth, spacing_mm) if fill else koch_snowflake_points(cx, cy, side, depth)
            sequences.append(seq)
            colors.append(cf)

            text = input("Text to embroider below snowflake: ").strip() or "COLUMBIA"
            baseline_y = cy + side * 0.7
            sx = cx - len(text) * 0.7 * 10 / 2.0
            ht = prompt_float("Text height", 10.0)
            ct = prompt_color("Text color (pick different for rubric)", "red")
            sequences.append(text_to_points(text, sx, baseline_y, ht, spacing_mm=spacing_mm))
            colors.append(ct)

    if not sequences:
        print("No patterns selected; nothing to write.")
        return

    extents = compute_extents_01mm(sequences)
    l, t, r, b = extents
    w_mm = (r - l) / 10.0 if r > l else 0
    h_mm = (b - t) / 10.0 if b > t else 0
    print(f"\nEstimated design size: {w_mm:.1f} x {h_mm:.1f} mm")
    if w_mm > 100 or h_mm > 100:
        print("WARNING: Design exceeds 100 x 100 mm. Consider reducing sizes.")

    print("\nWriting JEF file...")
    write_jef_multi(output_name, sequences, colors, hoop_code=hoop_code)
    print(f"Done. Saved to: {Path(output_name).absolute()}")


if __name__ == "__main__":
    main()
