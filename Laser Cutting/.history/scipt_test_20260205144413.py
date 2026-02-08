# generate_finger_joint_panel.py
# Uses ONLY file.write() and a mathematical formula to draw the edges (finger joints).
# Adjustable parameters: panel_width, panel_height, material_thickness (tab depth), finger_pitch, kerf, margin

import math

def make_even(n: int) -> int:
    n = max(2, int(n))
    return n if n % 2 == 0 else n + 1

def finger_count(length: float, pitch: float) -> int:
    return make_even(round(length / pitch))

def edge_points_axis_aligned(
    x: float, y: float,
    dx: int, dy: int,              # direction: one of (±1,0) or (0,±1)
    length: float,
    fingers: int,
    depth: float,                  # tab depth (usually = material thickness)
    outward_px: int, outward_py: int,  # outward perpendicular unit vector
    start_out: int                 # 0 or 1: whether we start offset-outward on this edge
):
    """
    Generate a zig-zag finger joint edge as a list of points (x,y),
    starting at (x,y), marching 'length' in direction (dx,dy).
    The edge alternates between offset=0 and offset=depth along outward perpendicular.
    """
    pts = [(x, y)]
    step = length / fingers

    # offset state: 0 => on the base line, 1 => pushed outward by 'depth'
    out = 1 if start_out else 0

    # If starting outward, first jump outward
    if out == 1:
        x += outward_px * depth
        y += outward_py * depth
        pts.append((x, y))

    for i in range(fingers):
        # move forward by one finger segment
        x += dx * step
        y += dy * step
        pts.append((x, y))

        # toggle offset at each finger boundary (except after the last move we still toggle,
        # because the next edge/corner will handle continuity cleanly)
        out ^= 1
        x += outward_px * (depth if out else -depth)
        y += outward_py * (depth if out else -depth)
        pts.append((x, y))

    # After loop, we're toggled one extra time; return to baseline at the end if needed
    # We want to end exactly on the baseline of the next corner (offset 0).
    if out == 1:
        # currently outward; step back to baseline
        x -= outward_px * depth
        y -= outward_py * depth
        pts.append((x, y))

    return pts, x, y

def points_to_path_d(points):
    # SVG path "M x y L x y ... Z"
    d = []
    for i, (x, y) in enumerate(points):
        cmd = "M" if i == 0 else "L"
        d.append(f"{cmd}{x:.3f} {y:.3f}")
    d.append("Z")
    return " ".join(d)

def generate_panel_svg(
    panel_width=200.0,             # mm (nominal interior width)
    panel_height=150.0,            # mm (nominal interior height)
    material_thickness=3.0,        # mm (tab depth)
    finger_pitch=9.0,              # mm (approx finger width; code chooses nearest even count)
    kerf=0.0,                      # mm (optional: positive expands; negative shrinks)
    margin=10.0,                   # mm
    filename="panel.svg"
):
    # Optional kerf compensation: expand (or shrink) the whole outline slightly.
    # Simple approach: treat kerf as extra depth (works decently for laser fits).
    depth = max(0.0, material_thickness + kerf)

    # Choose finger counts (even) from pitch
    nx = finger_count(panel_width, finger_pitch)
    ny = finger_count(panel_height, finger_pitch)

    # Build perimeter with four edges (bottom, right, top, left)
    # Coordinate system: SVG y+ downward.
    # Start at top-left corner of the nominal rectangle, but we’ll offset to keep everything positive.
    W = panel_width
    H = panel_height
    D = depth

    # Start baseline corner (0,0) then later translate by margin + D
    x0, y0 = 0.0, 0.0

    pts = [(x0, y0)]

    # Bottom edge: left->right, outward is +y (down) OR -y (up)?
    # For an "outer" contour that grows outward, choose outward to be DOWN on bottom edge.
    # But since we start at top-left, we'll do edges in clockwise order:
    # top edge (left->right), right edge (top->bottom), bottom edge (right->left), left edge (bottom->top)
    # This keeps outward consistent (outside is outward).
    # Top edge: left->right, outward is -y (up)
    top_pts, x, y = edge_points_axis_aligned(
        x0, y0, dx=1, dy=0, length=W, fingers=nx,
        depth=D, outward_px=0, outward_py=-1,
        start_out=0
    )
    pts = top_pts[:-1]  # avoid duplicating last point when chaining

    # Right edge: top->bottom, outward is +x (right)
    right_pts, x, y = edge_points_axis_aligned(
        x, y, dx=0, dy=1, length=H, fingers=ny,
        depth=D, outward_px=1, outward_py=0,
        start_out=0
    )
    pts += right_pts[1:-1]

    # Bottom edge: right->left, outward is +y (down)
    bottom_pts, x, y = edge_points_axis_aligned(
        x, y, dx=-1, dy=0, length=W, fingers=nx,
        depth=D, outward_px=0, outward_py=1,
        start_out=0
    )
    pts += bottom_pts[1:-1]

    # Left edge: bottom->top, outward is -x (left)
    left_pts, x, y = edge_points_axis_aligned(
        x, y, dx=0, dy=-1, length=H, fingers=ny,
        depth=D, outward_px=-1, outward_py=0,
        start_out=0
    )
    pts += left_pts[1:]  # include last to close

    # Translate so everything is positive and has a margin
    # The outline extends by +/-D, so include D in translation.
    tx = margin + D
    ty = margin + D
    pts = [(px + tx, py + ty) for (px, py) in pts]

    # Compute SVG size
    svg_w = W + 2 * (margin + D)
    svg_h = H + 2 * (margin + D)

    path_d = points_to_path_d(pts)

    # Write SVG using ONLY file.write()
    with open(filename, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<svg xmlns="http://www.w3.org/2000/svg" ')
        f.write(f'width="{svg_w:.2f}mm" height="{svg_h:.2f}mm" ')
        f.write(f'viewBox="0 0 {svg_w:.3f} {svg_h:.3f}">\n')
        f.write('  <path stroke="#ff0000" stroke-width="0.25" fill="none" ')
        f.write(f'd="{path_d}"/>\n')
        f.write('</svg>\n')

    print(f"Wrote {filename}")
    print(f"Panel: {panel_width} x {panel_height} mm | depth={depth} | fingers: nx={nx}, ny={ny}")

if __name__ == "__main__":
    # Change these:
    generate_panel_svg(
        panel_width=200.0,
        panel_height=150.0,
        material_thickness=3.0,
        finger_pitch=9.0,
        kerf=0.0,
        margin=10.0,
        filename="panel.svg"
    )