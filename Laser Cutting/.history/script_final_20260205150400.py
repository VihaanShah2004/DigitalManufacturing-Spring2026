# cuboid_6_faces_fingerjoints.py
# ONLY uses file.write() to output an SVG.
# User inputs: length (L), width (W), height (H) of the cuboid.
# Generates 6 laser-cut faces (Top/Bottom/Front/Back/Left/Right) with finger-joint edges
# so they assemble into the cuboid.
#
# FIX FOR YOUR ISSUE:
# - You need TWO “square” faces (TOP/BOTTOM) to be able to mate with side faces that have OUTER TABS.
# - That means TOP/BOTTOM must have SLOTS on the edges they mate with.
# - Also, side faces must complement each other on vertical edges (you cannot reuse one identical rectangle 4 times).
#
# This code assigns polarities per face edge so every shared edge is complementary.

import math

def make_even(n: int) -> int:
    n = max(2, int(n))
    return n if n % 2 == 0 else n + 1

def finger_count(edge_len: float, pitch: float) -> int:
    return make_even(round(edge_len / pitch))

def edge_points(
    x: float, y: float,
    dx: int, dy: int,                   # direction along edge: (±1,0) or (0,±1)
    length: float,
    fingers: int,
    depth: float,                       # + => tabs outward, - => slots inward
    outward_px: int, outward_py: int,    # outward normal (unit)
    start_out: int = 0
):
    """
    Returns: (points_list, end_x, end_y)
    Produces a zig-zag polyline for a finger-jointed edge.
    """
    pts = [(x, y)]
    step = length / fingers

    # out_state: 0 baseline, 1 offset by depth along outward normal
    out_state = 1 if start_out else 0

    # initial jump if starting outward
    if out_state == 1:
        x += outward_px * depth
        y += outward_py * depth
        pts.append((x, y))

    for _ in range(fingers):
        # forward segment
        x += dx * step
        y += dy * step
        pts.append((x, y))

        # toggle offset at each finger boundary
        out_state ^= 1
        x += outward_px * (depth if out_state else -depth)
        y += outward_py * (depth if out_state else -depth)
        pts.append((x, y))

    # ensure we end on baseline at the corner
    if out_state == 1:
        x -= outward_px * depth
        y -= outward_py * depth
        pts.append((x, y))

    return pts, x, y

def face_path_points(face_w, face_h, T, pitch, kerf, polarity):
    """
    Build a closed polygon (list of points) for one face with finger joints on all 4 sides.
    polarity: dict with keys ['top','right','bottom','left'] each in {+1,-1}
              +1 => tabs outward, -1 => slots inward
    """
    depth = max(0.0, T + kerf)
    nx = finger_count(face_w, pitch)
    ny = finger_count(face_h, pitch)

    x0, y0 = 0.0, 0.0

    # Top edge (L->R), outward is UP (0,-1) in SVG coords (y increases down), so use -1.
    top_pts, x, y = edge_points(
        x0, y0, dx=1, dy=0, length=face_w, fingers=nx,
        depth=polarity["top"] * depth,
        outward_px=0, outward_py=-1,
        start_out=0
    )
    pts = top_pts[:-1]

    # Right edge (T->B), outward is RIGHT (+1,0)
    right_pts, x, y = edge_points(
        x, y, dx=0, dy=1, length=face_h, fingers=ny,
        depth=polarity["right"] * depth,
        outward_px=1, outward_py=0,
        start_out=0
    )
    pts += right_pts[1:-1]

    # Bottom edge (R->L), outward is DOWN (0,+1)
    bottom_pts, x, y = edge_points(
        x, y, dx=-1, dy=0, length=face_w, fingers=nx,
        depth=polarity["bottom"] * depth,
        outward_px=0, outward_py=1,
        start_out=0
    )
    pts += bottom_pts[1:-1]

    # Left edge (B->T), outward is LEFT (-1,0)
    left_pts, x, y = edge_points(
        x, y, dx=0, dy=-1, length=face_h, fingers=ny,
        depth=polarity["left"] * depth,
        outward_px=-1, outward_py=0,
        start_out=0
    )
    pts += left_pts[1:]  # closes

    return pts, depth

def points_to_d(points, tx=0.0, ty=0.0):
    d = []
    for i, (x, y) in enumerate(points):
        if i == 0:
            d.append(f"M{(x+tx):.3f} {(y+ty):.3f}")
        else:
            d.append(f"L{(x+tx):.3f} {(y+ty):.3f}")
    d.append("Z")
    return " ".join(d)

def main():
    # --- USER INPUTS ---
    L = float(input("Enter cuboid LENGTH (mm): ").strip())
    W = float(input("Enter cuboid WIDTH  (mm): ").strip())
    H = float(input("Enter cuboid HEIGHT (mm): ").strip())

    # --- TUNABLE PARAMETERS ---
    T = 3.0             # material thickness (mm)
    finger_pitch = 9.0  # approx finger width (mm)
    kerf = 0.0          # optional depth tweak (mm)
    gap = 18.0          # spacing between pieces (mm)
    margin = 18.0       # page margin (mm)
    stroke = 0.25

    # --- FACES ---
    faces = {
        "TOP":    (L, W),
        "BOTTOM": (L, W),
        "FRONT":  (L, H),
        "BACK":   (L, H),
        "LEFT":   (W, H),
        "RIGHT":  (W, H),
    }

    # Polarity dict: +1 tabs outward, -1 slots inward
    P = {name: {"top": +1, "right": +1, "bottom": +1, "left": +1} for name in faces.keys()}

    # Helper: enforce a complementary mating pair
    # (A.edgeA tabs, B.edgeB slots)
    def mate(faceA, edgeA, faceB, edgeB):
        P[faceA][edgeA] = +1
        P[faceB][edgeB] = -1

    # ==========================================================
    # KEY CHANGE (fixes your remaining mismatch):
    #
    # 1) SIDE PANELS: you cannot have all four with identical vertical edges.
    #    We force a consistent wrap so adjacent sides complement.
    #
    # 2) TOP/BOTTOM: must have SLOTS on the perimeter edges that mate with
    #    side-panel TOP edges (which we set to TABS).
    # ==========================================================

    # --- Set side-panel vertical edges to complement around the loop ---
    # FRONT meets LEFT on its left edge, and meets RIGHT on its right edge
    mate("FRONT", "left",  "LEFT",  "right")
    mate("FRONT", "right", "RIGHT", "left")

    # BACK meets LEFT on its left edge, and meets RIGHT on its right edge
    mate("BACK", "left",   "LEFT",  "left")
    mate("BACK", "right",  "RIGHT", "right")

    # --- Top perimeter: side TOP edges are TABS; TOP face edges must be SLOTS ---
    mate("FRONT", "top", "TOP", "bottom")
    mate("RIGHT", "top", "TOP", "right")
    mate("BACK",  "top", "TOP", "top")
    mate("LEFT",  "top", "TOP", "left")

    # --- Bottom perimeter: side BOTTOM edges are TABS; BOTTOM face edges must be SLOTS ---
    mate("FRONT", "bottom", "BOTTOM", "top")
    mate("RIGHT", "bottom", "BOTTOM", "right")
    mate("BACK",  "bottom", "BOTTOM", "bottom")
    mate("LEFT",  "bottom", "BOTTOM", "left")

    # --- LAYOUT (separate cut pieces in a net-like arrangement) ---
    layout = {}

    top_w, top_h = faces["TOP"]
    front_w, front_h = faces["FRONT"]
    left_w, left_h = faces["LEFT"]
    right_w, right_h = faces["RIGHT"]
    back_w, back_h = faces["BACK"]

    # place middle row: LEFT FRONT RIGHT BACK
    x_front = margin + left_w + gap
    y_front = margin + top_h + gap

    layout["LEFT"]  = (margin, y_front)
    layout["FRONT"] = (x_front, y_front)
    layout["RIGHT"] = (x_front + front_w + gap, y_front)
    layout["BACK"]  = (layout["RIGHT"][0] + right_w + gap, y_front)

    # place TOP above FRONT, BOTTOM below FRONT
    layout["TOP"]    = (x_front, margin)
    layout["BOTTOM"] = (x_front, y_front + front_h + gap)

    # --- BUILD PATHS + BOUNDS ---
    paths = []
    max_x = 0.0
    max_y = 0.0

    for name, (fw, fh) in faces.items():
        pts, depth_used = face_path_points(fw, fh, T, finger_pitch, kerf, P[name])

        tx, ty = layout[name]
        tx += depth_used
        ty += depth_used

        d = points_to_d(pts, tx=tx, ty=ty)
        paths.append((name, d))

        max_x = max(max_x, tx + fw + 2 * depth_used)
        max_y = max(max_y, ty + fh + 2 * depth_used)

    svg_w = max_x + margin
    svg_h = max_y + margin

    # --- WRITE SVG (ONLY file.write) ---
    out = "cuboid_net.svg"
    with open(out, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<svg xmlns="http://www.w3.org/2000/svg" ')
        f.write(f'width="{svg_w:.2f}mm" height="{svg_h:.2f}mm" ')
        f.write(f'viewBox="0 0 {svg_w:.3f} {svg_h:.3f}">\n')

        for name, d in paths:
            f.write(f'  <path stroke="#ff0000" stroke-width="{stroke}" fill="none" d="{d}"/>\n')

        f.write('</svg>\n')

    print(f"\nWrote {out}")
    print(f"Faces: TOP/BOTTOM {L}x{W}, FRONT/BACK {L}x{H}, LEFT/RIGHT {W}x{H}")
    print(f"Params: T={T}mm, finger_pitch={finger_pitch}mm, kerf={kerf}mm")

if __name__ == "__main__":
    main()