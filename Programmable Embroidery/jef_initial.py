"""
JEF (Janome Embroidery Format) file generator.
Generates .jef files for use with Janome embroidery machines.
Supports circles, rectangles, and custom stitch patterns.
"""

import struct
from datetime import datetime
from math import cos, sin, pi
from pathlib import Path


# JEF thread color codes (1-78). Index 0 = Black, 1 = White, etc.
JEF_COLOR_CODES = {
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

# Stitch units: 1 unit = 0.1 mm. Max displacement per stitch = 127 units = 12.7 mm
MAX_STITCH_DELTA = 127
CMD_ESCAPE = 0x80
CMD_COLOR_CHANGE = 0x01
CMD_JUMP_TRIM = 0x02
CMD_END = 0x10


def _clamp_signed_byte(value: float) -> int:
    """Clamp to [-127, 127] for JEF stitch/jump displacement."""
    return max(-MAX_STITCH_DELTA, min(MAX_STITCH_DELTA, int(round(value))))


def _write_jef_header(
    f,
    stitch_offset: int,
    color_count: int,
    stitch_count: int,
    hoop_code: int = 0,
) -> None:
    """Write the 116-byte JEF file header."""
    # Offset 0: stitch offset (u32 LE)
    f.write(struct.pack("<I", stitch_offset))
    # Offset 4: flags (0x14)
    f.write(struct.pack("<I", 0x14))
    # Offset 8: date YYYYMMDD (8 bytes ASCII)
    f.write(datetime.now().strftime("%Y%m%d").encode("ascii").ljust(8)[:8])
    # Offset 16: time HHMMSSxx (8 bytes ASCII)
    f.write(datetime.now().strftime("%H%M%S00").encode("ascii").ljust(8)[:8])
    # Offset 24: version / padding (edutech: 1 char version + 1 u8 0x20; KDE: 4 bytes thread count at 24)
    # KDE says offset 24 = thread count. Use KDE layout.
    f.write(struct.pack("<I", color_count))   # offset 24: thread count
    f.write(struct.pack("<I", stitch_count))  # offset 28: stitch count (points length / 2 in some docs)
    f.write(struct.pack("<I", hoop_code))     # offset 32: hoop code
    # Offset 36-112: extent measurements (5 hoops × 4 values × 4 bytes = 80 bytes)
    # First hoop: use default 126x110 mm -> half extents in 0.1 mm: 630, 550
    extents_1 = (630, 550, 630, 550)  # left, top, right, bottom from center
    f.write(struct.pack("<iiii", *extents_1))
    # Hoops 2-5: -1 = not used
    for _ in range(4):
        f.write(struct.pack("<iiii", -1, -1, -1, -1))


def _write_thread_tables(f, color_codes: list[int]) -> None:
    """Write thread colour list and thread type list (each entry 4 bytes)."""
    for code in color_codes:
        f.write(struct.pack("<I", code))
    for _ in color_codes:
        f.write(struct.pack("<I", 0x0D))  # thread type / separator


def absolute_to_stitches(points: list[tuple[float, float]], units_per_mm: float = 10.0) -> bytes:
    """
    Convert a list of (x, y) positions in mm to JEF stitch bytes.
    Uses relative displacements; inserts JUMP (0x80 0x02 dx dy) when delta > 12.7 mm.
    """
    out = []
    units_per_mm = float(units_per_mm)  # 10 = 0.1 mm per unit
    px, py = 0.0, 0.0

    for x, y in points:
        dx = (x - px) * units_per_mm
        dy = (y - py) * units_per_mm
        px, py = x, y

        # If displacement too large, emit a jump
        if abs(dx) > MAX_STITCH_DELTA or abs(dy) > MAX_STITCH_DELTA:
            out.append(bytes([CMD_ESCAPE, CMD_JUMP_TRIM]))
            jx = _clamp_signed_byte(dx)
            jy = _clamp_signed_byte(dy)
            out.append(struct.pack("<bb", jx, jy))
            continue

        ix = _clamp_signed_byte(dx)
        iy = _clamp_signed_byte(dy)
        out.append(struct.pack("<bb", ix, iy))

    return b"".join(out)


def count_stitches(stitch_bytes: bytes) -> int:
    """Count number of stitch commands (excluding END). Each stitch = 2 bytes; commands = 2 or 4."""
    n = 0
    i = 0
    while i < len(stitch_bytes):
        if stitch_bytes[i] == CMD_ESCAPE:
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


def circle_points(
    center_x_mm: float,
    center_y_mm: float,
    radius_mm: float,
    num_stitches: int | None = None,
    stitch_spacing_mm: float = 0.5,
    close: bool = True,
) -> list[tuple[float, float]]:
    """
    Generate points along a circle in mm.
    Either specify num_stitches or stitch_spacing_mm (approximate).
    """
    if num_stitches is None:
        circumference = 2 * pi * radius_mm
        num_stitches = max(8, int(round(circumference / stitch_spacing_mm)))
    points = []
    for i in range(num_stitches):
        t = 2 * pi * i / num_stitches
        x = center_x_mm + radius_mm * cos(t)
        y = center_y_mm + radius_mm * sin(t)
        points.append((x, y))
    if close and num_stitches > 0:
        points.append(points[0])
    return points


def rectangle_points(
    left_mm: float,
    top_mm: float,
    width_mm: float,
    height_mm: float,
    stitch_spacing_mm: float = 0.5,
) -> list[tuple[float, float]]:
    """Generate points along a rectangle (one full loop)."""
    right = left_mm + width_mm
    bottom = top_mm + height_mm
    points = []
    # Top edge
    n_top = max(1, int(round(width_mm / stitch_spacing_mm)))
    for i in range(n_top + 1):
        points.append((left_mm + (right - left_mm) * i / n_top, top_mm))
    n_right = max(1, int(round(height_mm / stitch_spacing_mm)))
    for i in range(1, n_right + 1):
        points.append((right, top_mm + (bottom - top_mm) * i / n_right))
    n_bottom = max(1, int(round(width_mm / stitch_spacing_mm)))
    for i in range(1, n_bottom + 1):
        points.append((right - (right - left_mm) * i / n_bottom, bottom))
    n_left = max(1, int(round(height_mm / stitch_spacing_mm)))
    for i in range(1, n_left):
        points.append((left_mm, bottom - (bottom - top_mm) * i / n_left))
    return points


def star_points(
    center_x_mm: float,
    center_y_mm: float,
    outer_radius_mm: float,
    inner_radius_mm: float,
    num_points: int = 5,
    stitch_spacing_mm: float = 0.5,
) -> list[tuple[float, float]]:
    """Generate points along a star pattern."""
    points = []
    for i in range(num_points * 2):
        r = outer_radius_mm if i % 2 == 0 else inner_radius_mm
        t = pi * i / num_points - pi / 2  # start from top
        x = center_x_mm + r * cos(t)
        y = center_y_mm + r * sin(t)
        points.append((x, y))
    points.append(points[0])
    return points


def write_jef(
    path: str | Path,
    stitch_bytes: bytes,
    color_name: str = "black",
    hoop_code: int = 0,
) -> None:
    """
    Write a complete JEF file.
    stitch_bytes: raw stitch data ending with CMD_END (0x80 0x10).
    """
    path = Path(path)
    if not stitch_bytes.endswith(bytes([CMD_ESCAPE, CMD_END])):
        stitch_bytes = stitch_bytes + bytes([CMD_ESCAPE, CMD_END])

    color_code = JEF_COLOR_CODES.get(color_name.lower(), 1)
    color_count = 1
    stitch_count = count_stitches(stitch_bytes)
    stitch_offset = 116 + 8 * color_count

    with open(path, "wb") as f:
        _write_jef_header(f, stitch_offset, color_count, stitch_count, hoop_code)
        _write_thread_tables(f, [color_code])
        f.write(stitch_bytes)


def create_circle_jef(
    output_path: str | Path,
    center_x_mm: float = 0.0,
    center_y_mm: float = 0.0,
    radius_mm: float = 20.0,
    num_stitches: int | None = None,
    stitch_spacing_mm: float = 0.5,
    color: str = "black",
    hoop_code: int = 0,
) -> None:
    """Generate a JEF file containing a single circle."""
    points = circle_points(center_x_mm, center_y_mm, radius_mm, num_stitches, stitch_spacing_mm)
    stitch_bytes = absolute_to_stitches(points)
    write_jef(output_path, stitch_bytes, color, hoop_code)


def create_rectangle_jef(
    output_path: str | Path,
    left_mm: float = 0.0,
    top_mm: float = 0.0,
    width_mm: float = 30.0,
    height_mm: float = 20.0,
    stitch_spacing_mm: float = 0.5,
    color: str = "black",
    hoop_code: int = 0,
) -> None:
    """Generate a JEF file containing a rectangle outline."""
    points = rectangle_points(left_mm, top_mm, width_mm, height_mm, stitch_spacing_mm)
    stitch_bytes = absolute_to_stitches(points)
    write_jef(output_path, stitch_bytes, color, hoop_code)


def create_star_jef(
    output_path: str | Path,
    center_x_mm: float = 0.0,
    center_y_mm: float = 0.0,
    outer_radius_mm: float = 25.0,
    inner_radius_mm: float = 10.0,
    num_points: int = 5,
    stitch_spacing_mm: float = 0.5,
    color: str = "black",
    hoop_code: int = 0,
) -> None:
    """Generate a JEF file containing a star pattern."""
    points = star_points(center_x_mm, center_y_mm, outer_radius_mm, inner_radius_mm, num_points, stitch_spacing_mm)
    stitch_bytes = absolute_to_stitches(points)
    write_jef(output_path, stitch_bytes, color, hoop_code)


def create_custom_jef(
    output_path: str | Path,
    points: list[tuple[float, float]],
    color: str = "black",
    hoop_code: int = 0,
) -> None:
    """Generate a JEF file from a list of (x, y) points in mm."""
    stitch_bytes = absolute_to_stitches(points)
    write_jef(output_path, stitch_bytes, color, hoop_code)


def _prompt_float(prompt: str, default: float) -> float:
    """Ask user for a float; use default if they press Enter."""
    s = input(prompt).strip()
    return float(s) if s else default


def _prompt_int(prompt: str, default: int) -> int:
    """Ask user for an int; use default if they press Enter."""
    s = input(prompt).strip()
    return int(s) if s else default


if __name__ == "__main__":
    print("JEF Embroidery File Generator")
    print("Patterns: circle, rectangle, star")
    print()

    while True:
        pattern = input("Which pattern do you want to create? (circle / rectangle / star): ").strip().lower()
        if pattern in ("circle", "rectangle", "star"):
            break
        print("Please enter 'circle', 'rectangle', or 'star'.")

    output_name = input("Output filename (e.g. design.jef) [output.jef]: ").strip() or "output.jef"
    out = Path(output_name)
    if out.suffix.lower() != ".jef":
        out = out.with_suffix(".jef")

    color = input("Thread color (black, white, red, blue, green, yellow, pink, gold) [black]: ").strip().lower() or "black"
    if color not in JEF_COLOR_CODES:
        color = "black"

    hoop = _prompt_int("Hoop code (0=126x110mm, 1=50x50, 2=140x200, 3=126x110 spring, 4=230x200) [0]: ", 0)
    hoop = max(0, min(4, hoop))
    spacing = _prompt_float("Stitch spacing in mm [0.5]: ", 0.5)

    if pattern == "circle":
        cx = _prompt_float("Center X (mm) [0]: ", 0.0)
        cy = _prompt_float("Center Y (mm) [0]: ", 0.0)
        radius = _prompt_float("Radius (mm) [20]: ", 20.0)
        create_circle_jef(out, cx, cy, radius, stitch_spacing_mm=spacing, color=color, hoop_code=hoop)
        print(f"Created circle JEF: {out} (radius={radius} mm)")
    elif pattern == "rectangle":
        left = _prompt_float("Left (mm) [0]: ", 0.0)
        top = _prompt_float("Top (mm) [0]: ", 0.0)
        width = _prompt_float("Width (mm) [30]: ", 30.0)
        height = _prompt_float("Height (mm) [20]: ", 20.0)
        create_rectangle_jef(out, left, top, width, height, spacing, color, hoop)
        print(f"Created rectangle JEF: {out} ({width} x {height} mm)")
    else:  # star
        cx = _prompt_float("Center X (mm) [0]: ", 0.0)
        cy = _prompt_float("Center Y (mm) [0]: ", 0.0)
        outer = _prompt_float("Outer radius (mm) [25]: ", 25.0)
        inner = _prompt_float("Inner radius (mm) [10]: ", 10.0)
        points = _prompt_int("Number of points [5]: ", 5)
        create_star_jef(out, cx, cy, outer, inner, points, spacing, color, hoop)
        print(f"Created star JEF: {out} ({points}-point star)")
