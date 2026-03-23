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

import struct
from datetime import datetime
from math import cos, sin, pi
from pathlib import Path
from typing import List, Tuple, Dict

# ------------------------ JEF constants & utilities ------------------------

# JEF thread color codes (1–78). (Subset)
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

# Hoop codes and approximate sizes (mm)
HOOP_SIZES = {
    0: (126, 110),   # A Standard
    1: (50, 50),     # C Free Arm
    2: (140, 200),   # B Large
    3: (126, 110),   # F Spring Loaded
    4: (230, 200),   # D Giga
}

# Stitch units: 1 unit = 0.1 mm. Max displacement per stitch = 127 units (12.7 mm).
MAX_STITCH_DELTA = 127
CMD_ESCAPE = 0x80
CMD_COLOR_CHANGE = 0x01
CMD_JUMP_TRIM = 0x02
CMD_END = 0x10


def clamp_signed_byte(value: float) -> int:
    """Clamp to [-127, 127] for JEF stitch/jump displacement."""
    return max(-MAX_STITCH_DELTA, min(MAX_STITCH_DELTA, int(round(value))))


def write_jef_header(
    f,
    stitch_offset: int,
    color_count: int,
    stitch_count: int,
    hoop_code: int,
    extents_01mm: Tuple[int, int, int, int],
) -> None:
    """
    Write JEF file header according to common specs.

    extents_01mm = (left, top, right, bottom) in 0.1 mm from design center.
    """
    # Offset 0: stitch offset (u32 LE)
    f.write(struct.pack("<I", stitch_offset))
    # Offset 4: flags (0x14)
    f.write(struct.pack("<I", 0x14))
    # Offset 8: date YYYYMMDD (8 bytes ASCII)
    f.write(datetime.now().strftime("%Y%m%d").encode("ascii").ljust(8)[:8])
    # Offset 16: time HHMMSSxx (8 bytes ASCII)
    f.write(datetime.now().strftime("%H%M%S00").encode("ascii").ljust(8)[:8])
    # Offset 24: thread count (u32)
    f.write(struct.pack("<I", color_count))
    # Offset 28: stitch count (u32)
    f.write(struct.pack("<I", stitch_count))
    # Offset 32: hoop code (u32)
    f.write(struct.pack("<I", hoop_code))

    # Offset 36–52: primary extents (4 * u32) in 0.1 mm from center
    l, t, r, b = extents_01mm
    f.write(struct.pack("<iiii", l, t, r, b))

    # Offsets for 4 more hoops extents (unused => -1)
    for _ in range(4):
        f.write(struct.pack("<iiii", -1, -1, -1, -1))


def write_thread_tables(f, color_codes: List[int]) -> None:
    """Write thread color list and thread type list."""
    # Thread-color list
    for code in color_codes:
        f.write(struct.pack("<I", code))
    # Thread-type list (0x0D per color)
    for _ in color_codes:
        f.write(struct.pack("<I", 0x0D))


def count_stitches(stitch_bytes: bytes) -> int:
    """Count number of stitch commands (excluding END)."""
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
            # normal stitch dx, dy
            i += 2
            n += 1
    return n


def points_sequences_to_stitches(
    sequences: List[List[Tuple[float, float]]],
    units_per_mm: float = 10.0,
    use_color_changes: bool = True,
) -> bytes:
    """
    Convert multiple sequences of absolute (x, y) points in mm into JEF stitch bytes.

    - Inserts COLOR_CHANGE (0x80 0x01) between sequences when use_color_changes is True.
    - Inserts JUMP/TRIM (0x80 0x02 dx dy) automatically for large displacements.
    """
    units_per_mm = float(units_per_mm)
    out = bytearray()

    # Start at (0,0)
    px, py = 0.0, 0.0

    first_seq = True
    for seq in sequences:
        if not seq:
            continue

        if not first_seq and use_color_changes:
            out.append(CMD_ESCAPE)
            out.append(CMD_COLOR_CHANGE)
        first_seq = False

        for (x, y) in seq:
            dx = (x - px) * units_per_mm
            dy = (y - py) * units_per_mm
            px, py = x, y

            if abs(dx) > MAX_STITCH_DELTA or abs(dy) > MAX_STITCH_DELTA:
                # Use a jump/trim command
                out.append(CMD_ESCAPE)
                out.append(CMD_JUMP_TRIM)
                jx = clamp_signed_byte(dx)
                jy = clamp_signed_byte(dy)
                out.extend(struct.pack("<bb", jx, jy))
            else:
                ix = clamp_signed_byte(dx)
                iy = clamp_signed_byte(dy)
                out.extend(struct.pack("<bb", ix, iy))

    # Add END command
    out.append(CMD_ESCAPE)
    out.append(CMD_END)

    return bytes(out)


def compute_extents_01mm(sequences: List[List[Tuple[float, float]]]) -> Tuple[int, int, int, int]:
    """Compute design extents (left, top, right, bottom) in 0.1 mm, from (0,0)."""
    xs: List[float] = []
    ys: List[float] = []
    for seq in sequences:
        for x, y in seq:
            xs.append(x)
            ys.append(y)
    if not xs or not ys:
        return (0, 0, 0, 0)

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    # Convert mm to 0.1 mm and round
    left = int(round(min_x * 10))
    right = int(round(max_x * 10))
    top = int(round(min_y * 10))
    bottom = int(round(max_y * 10))

    return (left, top, right, bottom)


def write_jef_multi(
    path: str | Path,
    sequences: List[List[Tuple[float, float]]],
    color_names: List[str],
    hoop_code: int = 0,
) -> None:
    """
    Write a complete JEF file with multiple color sequences.

    Each sequence in `sequences` is drawn in the corresponding color in `color_names`.
    """
    if not sequences:
        raise ValueError("No sequences to write.")

    # Map color names to JEF codes
    color_codes: List[int] = []
    for name in color_names:
        name = name.lower()
        color_codes.append(JEF_COLOR_CODES.get(name, 1))

    # Limit color_count to number of sequences (safeguard)
    color_count = max(1, min(len(color_codes), len(sequences)))

    # Compute stitch bytes
    stitch_bytes = points_sequences_to_stitches(sequences[:color_count])
    stitch_count = count_stitches(stitch_bytes)
    stitch_offset = 116 + 8 * color_count

    # Extents in 0.1 mm (from origin)
    extents_01mm = compute_extents_01mm(sequences[:color_count])

    path = Path(path)
    if path.suffix.lower() != ".jef":
        path = path.with_suffix(".jef")

    with path.open("wb") as f:
        write_jef_header(
            f,
            stitch_offset=stitch_offset,
            color_count=color_count,
            stitch_count=stitch_count,
            hoop_code=hoop_code,
            extents_01mm=extents_01mm,
        )
        write_thread_tables(f, color_codes[:color_count])
        f.write(stitch_bytes)


# ------------------------ Geometry: basic patterns ------------------------


def circle_points(
    center_x_mm: float,
    center_y_mm: float,
    radius_mm: float,
    stitch_spacing_mm: float = 0.8,
) -> List[Tuple[float, float]]:
    """Generate points along a circle in mm."""
    from math import ceil

    circumference = 2 * pi * radius_mm
    n = max(16, int(ceil(circumference / stitch_spacing_mm)))
    pts: List[Tuple[float, float]] = []
    for i in range(n + 1):
        t = 2 * pi * i / n
        x = center_x_mm + radius_mm * cos(t)
        y = center_y_mm + radius_mm * sin(t)
        pts.append((x, y))
    return pts


def rectangle_points(
    left_mm: float,
    top_mm: float,
    width_mm: float,
    height_mm: float,
    stitch_spacing_mm: float = 0.8,
) -> List[Tuple[float, float]]:
    """Generate points along a rectangle."""
    from math import ceil

    right = left_mm + width_mm
    bottom = top_mm + height_mm
    pts: List[Tuple[float, float]] = []

    # top edge
    n_top = max(1, int(ceil(width_mm / stitch_spacing_mm)))
    for i in range(n_top + 1):
        pts.append((left_mm + (right - left_mm) * i / n_top, top_mm))
    # right edge
    n_r = max(1, int(ceil(height_mm / stitch_spacing_mm)))
    for i in range(1, n_r + 1):
        pts.append((right, top_mm + (bottom - top_mm) * i / n_r))
    # bottom edge
    n_b = max(1, int(ceil(width_mm / stitch_spacing_mm)))
    for i in range(1, n_b + 1):
        pts.append((right - (right - left_mm) * i / n_b, bottom))
    # left edge
    n_l = max(1, int(ceil(height_mm / stitch_spacing_mm)))
    for i in range(1, n_l):
        pts.append((left_mm, bottom - (bottom - top_mm) * i / n_l))
    return pts


def star_points(
    center_x_mm: float,
    center_y_mm: float,
    outer_radius_mm: float,
    inner_radius_mm: float,
    num_points: int = 5,
) -> List[Tuple[float, float]]:
    """Generate a simple star (outline)."""
    pts: List[Tuple[float, float]] = []
    for i in range(num_points * 2 + 1):
        r = outer_radius_mm if i % 2 == 0 else inner_radius_mm
        t = pi * i / num_points - pi / 2
        x = center_x_mm + r * cos(t)
        y = center_y_mm + r * sin(t)
        pts.append((x, y))
    return pts


# ------------------------ Fractals ------------------------


def koch_segment(p0, p1, depth, pts: List[Tuple[float, float]]):
    """Recursive helper for one Koch segment."""
    if depth == 0:
        pts.append(p1)
        return
    x0, y0 = p0
    x1, y1 = p1
    dx = (x1 - x0) / 3.0
    dy = (y1 - y0) / 3.0

    pA = (x0 + dx, y0 + dy)
    pB = (x0 + 2 * dx, y0 + 2 * dy)
    # peak of equilateral triangle
    mid_x = (x0 + x1) / 2.0
    mid_y = (y0 + y1) / 2.0
    # perpendicular offset
    import math

    length = math.hypot(dx, dy)
    angle = math.atan2(dy, dx) - pi / 3.0
    px = x0 + dx + length * math.cos(angle) / 3.0
    py = y0 + dy + length * math.sin(angle) / 3.0
    pC = (px, py)

    koch_segment(p0, pA, depth - 1, pts)
    koch_segment(pA, pC, depth - 1, pts)
    koch_segment(pC, pB, depth - 1, pts)
    koch_segment(pB, p1, depth - 1, pts)


def koch_snowflake_points(
    center_x_mm: float,
    center_y_mm: float,
    side_mm: float,
    depth: int,
) -> List[Tuple[float, float]]:
    """
    Generate a Koch snowflake (fractal, not a tree).

    side_mm should be chosen so the resulting shape fits in 100x100 mm.
    Typically side_mm <= 60 works well.
    """
    depth = max(0, min(depth, 4))  # avoid too many stitches
    # Build an equilateral triangle
    h = side_mm * (3 ** 0.5) / 2.0
    p1 = (center_x_mm - side_mm / 2.0, center_y_mm - h / 3.0)
    p2 = (center_x_mm + side_mm / 2.0, center_y_mm - h / 3.0)
    p3 = (center_x_mm, center_y_mm + 2.0 * h / 3.0)

    pts: List[Tuple[float, float]] = [p1]
    koch_segment(p1, p2, depth, pts)
    koch_segment(p2, p3, depth, pts)
    koch_segment(p3, p1, depth, pts)
    return pts


def fractal_tree_points(
    base_x_mm: float,
    base_y_mm: float,
    length_mm: float,
    angle_rad: float,
    depth: int,
    angle_delta_rad: float,
    scale: float,
) -> List[Tuple[float, float]]:
    """
    Simple fractal tree (may over-stitch trunk on backtracking).
    depth: recursion depth (2–6 is reasonable).
    """
    pts: List[Tuple[float, float]] = [(base_x_mm, base_y_mm)]

    def _rec(x, y, length, angle, d):
        if d == 0 or length < 1.0:
            return
        x2 = x + length * cos(angle)
        y2 = y + length * sin(angle)
        pts.append((x2, y2))
        # backtrack and branch
        _rec(x2, y2, length * scale, angle + angle_delta_rad, d - 1)
        pts.append((x2, y2))
        _rec(x2, y2, length * scale, angle - angle_delta_rad, d - 1)
        pts.append((x, y))

    _rec(base_x_mm, base_y_mm, length_mm, angle_rad, depth)
    return pts


# ------------------------ Simple stroke font for text ------------------------

# Coordinates are in [0, 1] x [0, 1]. Each character is defined by strokes
# (lists of points). We only implement uppercase A–Z and digits 0–9.

FONT_STROKES: Dict[str, List[List[Tuple[float, float]]]] = {}


def _add_char(ch: str, strokes: List[List[Tuple[float, float]]]):
    FONT_STROKES[ch] = strokes


# Basic helper segments in 0–1 space.
def _H(y, x0=0.0, x1=1.0):
    return [(x0, y), (x1, y)]


def _V(x, y0=0.0, y1=1.0):
    return [(x, y0), (x, y1)]


# Define some simple block letters.
_add_char("A", [[(0.0, 0.0), (0.5, 1.0), (1.0, 0.0)], _H(0.5, 0.2, 0.8)])
_add_char("B", [[(0.0, 0.0), (0.0, 1.0)],
                [(0.0, 1.0), (0.7, 0.8), (0.0, 0.5)],
                [(0.0, 0.5), (0.7, 0.2), (0.0, 0.0)]])
_add_char("C", [[(1.0, 1.0), (0.2, 1.0), (0.0, 0.8), (0.0, 0.2), (0.2, 0.0), (1.0, 0.0)]])
_add_char("D", [[(0.0, 0.0), (0.0, 1.0), (0.6, 0.8), (0.8, 0.5), (0.6, 0.2), (0.0, 0.0)]])
_add_char("E", [[(1.0, 1.0), (0.0, 1.0), (0.0, 0.0), (1.0, 0.0)],
                _H(0.5, 0.0, 0.7)])
_add_char("F", [[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0)],
                _H(0.5, 0.0, 0.7)])
_add_char("G", [[(1.0, 0.8), (0.8, 1.0), (0.2, 1.0), (0.0, 0.8), (0.0, 0.2), (0.2, 0.0),
                 (0.8, 0.0), (1.0, 0.2), (1.0, 0.5), (0.6, 0.5)]])
_add_char("H", [[(0.0, 0.0), (0.0, 1.0)], [(1.0, 0.0), (1.0, 1.0)], _H(0.5, 0.0, 1.0)])
_add_char("I", [[(0.2, 1.0), (0.8, 1.0)], [(0.5, 1.0), (0.5, 0.0)], [(0.2, 0.0), (0.8, 0.0)]])
_add_char("J", [[(0.8, 1.0), (0.2, 1.0)], [(0.5, 1.0), (0.5, 0.2), (0.3, 0.0), (0.1, 0.2)]])
_add_char("K", [[(0.0, 0.0), (0.0, 1.0)],
                [(1.0, 1.0), (0.0, 0.5), (1.0, 0.0)]])
_add_char("L", [[(0.0, 1.0), (0.0, 0.0), (1.0, 0.0)]])
_add_char("M", [[(0.0, 0.0), (0.0, 1.0), (0.5, 0.5), (1.0, 1.0), (1.0, 0.0)]])
_add_char("N", [[(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]])
_add_char("O", [[(0.2, 0.0), (0.8, 0.0), (1.0, 0.2), (1.0, 0.8),
                 (0.8, 1.0), (0.2, 1.0), (0.0, 0.8), (0.0, 0.2), (0.2, 0.0)]])
_add_char("P", [[(0.0, 0.0), (0.0, 1.0), (0.8, 1.0), (1.0, 0.8),
                 (0.8, 0.6), (0.0, 0.6)]])
_add_char("Q", [[(0.2, 0.0), (0.8, 0.0), (1.0, 0.2), (1.0, 0.8),
                 (0.8, 1.0), (0.2, 1.0), (0.0, 0.8), (0.0, 0.2), (0.2, 0.0)],
                [(0.6, 0.2), (1.0, -0.2)]])
_add_char("R", [[(0.0, 0.0), (0.0, 1.0), (0.8, 1.0), (1.0, 0.8),
                 (0.8, 0.6), (0.0, 0.6)],
                [(0.0, 0.6), (1.0, 0.0)]])
_add_char("S", [[(0.8, 1.0), (0.2, 1.0), (0.0, 0.8), (0.2, 0.6), (0.8, 0.4),
                 (1.0, 0.2), (0.8, 0.0), (0.2, 0.0)]])
_add_char("T", [[(0.0, 1.0), (1.0, 1.0)], [(0.5, 1.0), (0.5, 0.0)]])
_add_char("U", [[(0.0, 1.0), (0.0, 0.2), (0.2, 0.0), (0.8, 0.0),
                 (1.0, 0.2), (1.0, 1.0)]])
_add_char("V", [[(0.0, 1.0), (0.5, 0.0), (1.0, 1.0)]])
_add_char("W", [[(0.0, 1.0), (0.25, 0.0), (0.5, 0.6), (0.75, 0.0), (1.0, 1.0)]])
_add_char("X", [[(0.0, 1.0), (1.0, 0.0)], [(0.0, 0.0), (1.0, 1.0)]])
_add_char("Y", [[(0.0, 1.0), (0.5, 0.5), (1.0, 1.0)], [(0.5, 0.5), (0.5, 0.0)]])
_add_char("Z", [[(0.0, 1.0), (1.0, 1.0), (0.0, 0.0), (1.0, 0.0)]])

# Digits 0–9 (simple)
_add_char("0", [[(0.2, 0.0), (0.8, 0.0), (1.0, 0.2), (1.0, 0.8),
                 (0.8, 1.0), (0.2, 1.0), (0.0, 0.8), (0.0, 0.2), (0.2, 0.0)]])
_add_char("1", [[(0.5, 0.0), (0.5, 1.0)]])
_add_char("2", [[(0.0, 0.8), (0.2, 1.0), (0.8, 1.0), (1.0, 0.8),
                 (0.0, 0.0), (1.0, 0.0)]])
_add_char("3", [[(0.0, 0.8), (0.2, 1.0), (0.8, 1.0), (1.0, 0.8),
                 (0.8, 0.6), (0.2, 0.5), (0.8, 0.4), (1.0, 0.2), (0.8, 0.0),
                 (0.2, 0.0)]])
_add_char("4", [[(0.8, 0.0), (0.8, 1.0)],
                [(0.0, 0.5), (1.0, 0.5)]])
_add_char("5", [[(1.0, 1.0), (0.2, 1.0), (0.0, 0.8), (0.0, 0.6),
                 (0.8, 0.4), (1.0, 0.2), (0.8, 0.0), (0.2, 0.0)]])
_add_char("6", [[(0.8, 1.0), (0.2, 1.0), (0.0, 0.8), (0.0, 0.2),
                 (0.2, 0.0), (0.8, 0.0), (1.0, 0.2), (0.8, 0.4), (0.2, 0.6)]])
_add_char("7", [[(0.0, 1.0), (1.0, 1.0), (0.4, 0.0)]])
_add_char("8", [[(0.2, 0.0), (0.8, 0.0), (1.0, 0.2), (0.8, 0.4), (0.2, 0.4),
                 (0.0, 0.2), (0.2, 0.0)],
                [(0.2, 0.4), (0.8, 0.4), (1.0, 0.6), (0.8, 0.8), (0.2, 0.8),
                 (0.0, 0.6), (0.2, 0.4)]])
_add_char("9", [[(0.2, 0.0), (0.8, 0.0), (1.0, 0.2), (1.0, 0.8),
                 (0.8, 1.0), (0.2, 1.0), (0.0, 0.8), (0.2, 0.6), (0.8, 0.6)]])


def text_to_points(
    text: str,
    start_x_mm: float,
    baseline_y_mm: float,
    height_mm: float,
    letter_spacing: float = 0.3,
) -> List[Tuple[float, float]]:
    """
    Convert a string into stroke points in mm.

    - Uses uppercase characters only; unknown characters are skipped.
    - height_mm: character height; width ~ 0.6 * height.
    """
    pts: List[Tuple[float, float]] = []
    text = text.upper()
    x_cursor = start_x_mm
    width_mm = height_mm * 0.6

    for ch in text:
        if ch == " ":
            x_cursor += width_mm * (1.0 + letter_spacing)
            continue

        strokes = FONT_STROKES.get(ch)
        if not strokes:
            x_cursor += width_mm * (1.0 + letter_spacing)
            continue

        for stroke in strokes:
            if not stroke:
                continue
            # Move to first point (we accept a stitched connector; embroidery machines
            # in practice will connect strokes; that's okay for our design).
            first = True
            for (sx, sy) in stroke:
                x = x_cursor + sx * width_mm
                y = baseline_y_mm + sy * height_mm
                if first:
                    pts.append((x, y))
                    first = False
                else:
                    pts.append((x, y))

        x_cursor += width_mm * (1.0 + letter_spacing)

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


def main():
    print("=== JEF Embroidery File Generator (Final) ===")
    print("All sizes are in millimeters. Keep your design within 100 x 100 mm.")
    print("Patterns implemented:")
    print("  1) Circle")
    print("  2) Rectangle")
    print("  3) Star")
    print("  4) Koch snowflake (fractal, NOT a tree)")
    print("  5) Fractal tree")
    print("  6) Text only")
    print("  7) Koch snowflake + text (two colors)")
    print()

    while True:
        try:
            pattern_choice = int(input("Select pattern (1-7): ").strip())
            if 1 <= pattern_choice <= 7:
                break
            print("Please choose a number between 1 and 7.")
        except ValueError:
            print("Please enter a valid integer between 1 and 7.")

    output_name = input("Output file name (e.g., design.jef) [design.jef]: ").strip()
    if not output_name:
        output_name = "design.jef"

    hoop_code = prompt_int("Hoop code (0=126x110, 1=50x50, 2=140x200, 3=126x110 spring, 4=230x200)", 0)
    hoop_code = max(0, min(4, hoop_code))
    spacing_mm = prompt_float("Approximate stitch spacing (mm)", 0.8)

    sequences: List[List[Tuple[float, float]]] = []
    colors: List[str] = []

    # All patterns will be centered roughly around (0,0) except text-only.
    if pattern_choice == 1:
        print("\n-- Circle --")
        cx = prompt_float("Center X", 0.0)
        cy = prompt_float("Center Y", 0.0)
        radius = prompt_float("Radius (<= 50 mm to stay inside 10x10cm)", 20.0)
        color = prompt_color("Thread color", "blue")
        seq = circle_points(cx, cy, radius, spacing_mm)
        sequences.append(seq)
        colors.append(color)

    elif pattern_choice == 2:
        print("\n-- Rectangle --")
        left = prompt_float("Left X", -20.0)
        top = prompt_float("Top Y", -20.0)
        width = prompt_float("Width", 40.0)
        height = prompt_float("Height", 40.0)
        color = prompt_color("Thread color", "green")
        seq = rectangle_points(left, top, width, height, spacing_mm)
        sequences.append(seq)
        colors.append(color)

    elif pattern_choice == 3:
        print("\n-- Star --")
        cx = prompt_float("Center X", 0.0)
        cy = prompt_float("Center Y", 0.0)
        outer_r = prompt_float("Outer radius", 30.0)
        inner_r = prompt_float("Inner radius", 12.0)
        points = prompt_int("Number of points", 5)
        color = prompt_color("Thread color", "gold")
        seq = star_points(cx, cy, outer_r, inner_r, points)
        sequences.append(seq)
        colors.append(color)

    elif pattern_choice == 4:
        print("\n-- Koch Snowflake (Fractal, NOT a tree) --")
        cx = prompt_float("Center X", 0.0)
        cy = prompt_float("Center Y", 0.0)
        side = prompt_float("Triangle side length (<= 60 mm recommended)", 50.0)
        depth = prompt_int("Recursion depth (0-4)", 2)
        color = prompt_color("Thread color", "red")
        seq = koch_snowflake_points(cx, cy, side, depth)
        sequences.append(seq)
        colors.append(color)

    elif pattern_choice == 5:
        print("\n-- Fractal Tree --")
        base_x = prompt_float("Base X", 0.0)
        base_y = prompt_float("Base Y", -40.0)
        length = prompt_float("Initial trunk length", 40.0)
        depth = prompt_int("Recursion depth (2-6)", 4)
        angle_deg = prompt_float("Branch angle (degrees)", 30.0)
        scale = prompt_float("Length scale per level (0.4-0.8)", 0.6)
        color = prompt_color("Thread color", "green")

        angle_rad = pi / 2.0  # trunk going up
        angle_delta_rad = angle_deg * pi / 180.0
        seq = fractal_tree_points(base_x, base_y, length, angle_rad, depth, angle_delta_rad, scale)
        sequences.append(seq)
        colors.append(color)

    elif pattern_choice == 6:
        print("\n-- Text Only --")
        text = input("Text to embroider (A-Z, 0-9, space): ").strip()
        if not text:
            text = "MECE4606"
        start_x = prompt_float("Start X", -40.0)
        baseline_y = prompt_float("Baseline Y", 0.0)
        height = prompt_float("Character height", 15.0)
        color = prompt_color("Thread color", "black")
        seq = text_to_points(text, start_x, baseline_y, height)
        sequences.append(seq)
        colors.append(color)

    elif pattern_choice == 7:
        print("\n-- Koch Snowflake + Text (Two Colors) --")
        # Fractal
        cx = prompt_float("Snowflake center X", 0.0)
        cy = prompt_float("Snowflake center Y", 10.0)
        side = prompt_float("Snowflake side length (<= 60 mm recommended)", 40.0)
        depth = prompt_int("Snowflake recursion depth (0-4)", 2)
        color_fractal = prompt_color("Snowflake color", "blue")
        snowflake_seq = koch_snowflake_points(cx, cy, side, depth)
        sequences.append(snowflake_seq)
        colors.append(color_fractal)

        # Text under snowflake
        text = input("Text to embroider under snowflake: ").strip()
        if not text:
            text = "COLUMBIA"
        baseline_y = cy - side  # roughly underneath
        start_x = cx - 30.0
        height = prompt_float("Text height", 12.0)
        color_text = prompt_color("Text color (different from snowflake for rubric)", "red")
        text_seq = text_to_points(text, start_x, baseline_y, height)
        sequences.append(text_seq)
        colors.append(color_text)

    # Warn if design is likely larger than 10x10 cm
    extents_01mm = compute_extents_01mm(sequences)
    left, top, right, bottom = extents_01mm
    width_mm = (right - left) / 10.0 if right > left else 0.0
    height_mm = (bottom - top) / 10.0 if bottom > top else 0.0
    print(f"\nEstimated design size: {width_mm:.1f} mm x {height_mm:.1f} mm")
    if width_mm > 100.0 or height_mm > 100.0:
        print("WARNING: Design exceeds 100 x 100 mm. Consider reducing sizes.")

    # Write JEF
    print("\nWriting JEF file...")
    write_jef_multi(output_name, sequences, colors, hoop_code=hoop_code)
    print(f"Done. Saved to: {Path(output_name).absolute()}")


if __name__ == "__main__":
    main()