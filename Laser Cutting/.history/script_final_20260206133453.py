#Vihaan Shah
#UNI: vvs2119
#MECE4606 Digital Manufacturing
#Laser Cutting Project
#
# Generates 6 panels with finger joints and (optional) embeds a PNG image centered on one panel.
# Writes SVG using ONLY file.write().

import base64
import os

# =========================
# Gather Input
# =========================
try:
    x = float(input("Type x coordinate to start: "))
    y = float(input("Type y coordinate to start: "))
    z = float(input("Type z coordinate to start: "))
    length = float(input("Type length (mm): "))   # currently unused in this 6-piece layout
    width  = float(input("Type width  (mm): "))
    height = float(input("Type height (mm): "))
    stroke_width = 0.25
except ValueError:
    print("Invalid input. All values must be numbers.")
    exit()

if width < 100 or height < 100 or length < 100:
    print("Invalid input. Length, width, and height must be at least 100 mm.")
    exit()
if stroke_width <= 0:
    print("Invalid input. Stroke width must be greater than 0.")
    exit()

# =========================
# Layout sizing
# =========================
w = width
h = height
gap = 100

svg_width  = 3 * w + 2 * gap
svg_height = 2 * h + gap

# =========================
# Material/tab parameters
# =========================
material_thickness = 3.0
tab_width = 9.0
corner_left = 6.5
corner_right = 12.5

mt = material_thickness
tw = tab_width
cl = corner_left
cr = corner_right

# =========================
# Helpers
# =========================
def points_to_polyline(points):
    return " ".join(f"{px},{py}" for px, py in points)

def _segments_count(edge_len):
    tab_section = edge_len - cl - cr
    n = int(round(tab_section / tw))
    if n < 2:
        n = 2
    return n

def read_image_as_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except:
        return None

def parse_png_size(path):
    """
    Returns (width_px, height_px) from PNG header (IHDR).
    No external libs, no PIL.
    """
    try:
        with open(path, "rb") as f:
            sig = f.read(8)
            if sig != b"\x89PNG\r\n\x1a\n":
                return None, None
            _len = f.read(4)
            ctype = f.read(4)
            if ctype != b"IHDR":
                return None, None
            ihdr = f.read(13)
            w_px = int.from_bytes(ihdr[0:4], "big")
            h_px = int.from_bytes(ihdr[4:8], "big")
            return w_px, h_px
    except:
        return None, None

# ==========================================================
# Panel generator with per-edge TAB/SLOT control
# slot_parity controls which segments get slots:
#   slot_parity=0 => slots on even indices (0,2,4,...)
#   slot_parity=1 => slots on odd  indices (1,3,5,...)
# ==========================================================
def generate_panel(face_w, face_h, edge_mode, slot_parity=0):
    """
    edge_mode: dict with keys {"top","right","bottom","left"} each in {"TAB","SLOT"}
      TAB  => protrude outward on odd segments
      SLOT => indent inward on slot_parity segments
    """
    half_w = face_w / 2.0
    half_h = face_h / 2.0

    n_w = _segments_count(face_w)
    n_h = _segments_count(face_h)

    pts = []

    # ---------- TOP edge ----------
    x0, y0 = -half_w,  half_h
    pts.append((x0, y0))
    x = x0 + cl
    y = y0
    pts.append((x, y))

    for i in range(n_w):
        if edge_mode["top"] == "TAB":
            if i % 2 == 1:
                pts.append((x, y + mt))
                x += tw
                pts.append((x, y + mt))
                pts.append((x, y))
            else:
                x += tw
                pts.append((x, y))
        else:  # SLOT
            if i % 2 == slot_parity:
                pts.append((x, y - mt))
                x += tw
                pts.append((x, y - mt))
                pts.append((x, y))
            else:
                x += tw
                pts.append((x, y))

    x = half_w
    pts.append((x, y))

    # ---------- RIGHT edge ----------
    y = half_h - cl
    pts.append((x, y))

    for i in range(n_h):
        if edge_mode["right"] == "TAB":
            if i % 2 == 1:
                pts.append((x + mt, y))
                y -= tw
                pts.append((x + mt, y))
                pts.append((x, y))
            else:
                y -= tw
                pts.append((x, y))
        else:  # SLOT
            if i % 2 == slot_parity:
                pts.append((x - mt, y))
                y -= tw
                pts.append((x - mt, y))
                pts.append((x, y))
            else:
                y -= tw
                pts.append((x, y))

    y = -half_h
    pts.append((x, y))

    # ---------- BOTTOM edge ----------
    x = half_w - cl
    pts.append((x, y))

    for i in range(n_w):
        if edge_mode["bottom"] == "TAB":
            if i % 2 == 1:
                pts.append((x, y - mt))
                x -= tw
                pts.append((x, y - mt))
                pts.append((x, y))
            else:
                x -= tw
                pts.append((x, y))
        else:  # SLOT
            if i % 2 == slot_parity:
                pts.append((x, y + mt))
                x -= tw
                pts.append((x, y + mt))
                pts.append((x, y))
            else:
                x -= tw
                pts.append((x, y))

    x = -half_w
    pts.append((x, y))

    # ---------- LEFT edge ----------
    y = -half_h + cl
    pts.append((x, y))

    for i in range(n_h):
        if edge_mode["left"] == "TAB":
            if i % 2 == 1:
                pts.append((x - mt, y))
                y += tw
                pts.append((x - mt, y))
                pts.append((x, y))
            else:
                y += tw
                pts.append((x, y))
        else:  # SLOT
            if i % 2 == slot_parity:
                pts.append((x + mt, y))
                y += tw
                pts.append((x + mt, y))
                pts.append((x, y))
            else:
                y += tw
                pts.append((x, y))

    y = half_h
    pts.append((x, y))

    return pts

# =========================
# EDGE MAPS
# =========================
EDGE_MAP_RECT   = {"top": "TAB",  "right": "TAB",  "bottom": "TAB",  "left": "TAB"}
EDGE_MAP_SQUARE = {"top": "SLOT", "right": "SLOT", "bottom": "SLOT", "left": "SLOT"}

# =========================
# Generate panels
# =========================
rect_pts_A = generate_panel(w, h, EDGE_MAP_RECT)
rect_pts_B = generate_panel(w, h, EDGE_MAP_RECT)

# squares: slots start on ODD segments so they align to rect odd tabs
square_pts = generate_panel(w, w, EDGE_MAP_SQUARE, slot_parity=1)

rect_points_str_A = points_to_polyline(rect_pts_A)
rect_points_str_B = points_to_polyline(rect_pts_B)
square_points_str = points_to_polyline(square_pts)

# =========================
# Ask for optional PNG artwork
# =========================
add_art = input("Add a PNG image onto one face? (y/n): ").strip().lower()

png_data = None
png_w_px = None
png_h_px = None
art_target = None

# mm margin inside the panel for the image bounding box
art_margin = 10.0

if add_art == "y":
    png_path = input("Enter path to PNG file (e.g. /Users/.../image.png): ").strip()

    png_data = read_image_as_base64(png_path)
    png_w_px, png_h_px = parse_png_size(png_path)

    if png_data is None or png_w_px is None or png_h_px is None:
        print("Could not read/parse PNG file. Skipping image.")
        png_data = None
        png_w_px = None
        png_h_px = None
    else:
        print("Choose which panel to place it on:")
        print("  A1 = top-left rectangle")
        print("  A2 = top-middle rectangle")
        print("  B1 = bottom-left rectangle")
        print("  B2 = bottom-middle rectangle")
        print("  S1 = top-right square")
        print("  S2 = bottom-right square")

        art_target = input("Type one of: A1 A2 B1 B2 S1 S2: ").strip().upper()
        if art_target not in {"A1","A2","B1","B2","S1","S2"}:
            print("Invalid panel choice. Skipping image.")
            png_data = None
            art_target = None

# =========================
# SVG sizing and margins
# =========================
tab_margin = mt + 5
total_w = svg_width + 2 * tab_margin
total_h = svg_height + 2 * tab_margin
view_w = total_w
view_h = total_h

# =========================
# Panel placement coordinates
# =========================
base_x = tab_margin + w / 2
base_y = tab_margin + h / 2

panel_centers = {
    "A1": (base_x, base_y),
    "A2": (base_x + w + gap, base_y),
    "B1": (base_x, base_y + h + gap),
    "B2": (base_x + w + gap, base_y + h + gap),
    "S1": (tab_margin + w/2 + 2*w + 2*gap, tab_margin + w/2),
    "S2": (tab_margin + w/2 + 2*w + 2*gap, tab_margin + w/2 + h + gap),
}

panel_sizes = {
    "A1": (w, h),
    "A2": (w, h),
    "B1": (w, h),
    "B2": (w, h),
    "S1": (w, w),
    "S2": (w, w),
}

# =========================
# Write SVG (ONLY file.write)
# =========================
file = open("gcode_file.svg", "w", encoding="utf-8")
file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" ')
file.write('xmlns:xlink="http://www.w3.org/1999/xlink" ')
file.write(f'viewBox="0 0 {view_w} {view_h}" width="{view_w}mm" height="{view_h}mm">\n')

# ---- CUT LINES group (red) ----
file.write(f'  <g stroke="red" stroke-width="{stroke_width}" fill="none">\n')

file.write(f'    <g transform="translate({panel_centers["A1"][0]}, {panel_centers["A1"][1]})">\n')
file.write(f'      <polygon points="{rect_points_str_A}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({panel_centers["A2"][0]}, {panel_centers["A2"][1]})">\n')
file.write(f'      <polygon points="{rect_points_str_B}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({panel_centers["B1"][0]}, {panel_centers["B1"][1]})">\n')
file.write(f'      <polygon points="{rect_points_str_B}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({panel_centers["B2"][0]}, {panel_centers["B2"][1]})">\n')
file.write(f'      <polygon points="{rect_points_str_A}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({panel_centers["S1"][0]}, {panel_centers["S1"][1]})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({panel_centers["S2"][0]}, {panel_centers["S2"][1]})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write('  </g>\n')  # end cut group

# ---- PNG artwork (centered, scaled, clipped) ----
if png_data is not None and art_target is not None:
    cx, cy = panel_centers[art_target]
    pw, ph = panel_sizes[art_target]

    usable_w = max(1.0, pw - 2 * art_margin)
    usable_h = max(1.0, ph - 2 * art_margin)

    img_aspect = png_w_px / png_h_px
    box_aspect = usable_w / usable_h

    if img_aspect >= box_aspect:
        img_w = usable_w
        img_h = usable_w / img_aspect
    else:
        img_h = usable_h
        img_w = usable_h * img_aspect

    x_img = cx - img_w / 2.0
    y_img = cy - img_h / 2.0

    clip_id = f"clip_{art_target}"

    file.write('  <defs>\n')
    file.write(f'    <clipPath id="{clip_id}">\n')
    file.write(
        f'      <rect x="{(cx-usable_w/2):.3f}" y="{(cy-usable_h/2):.3f}" '
        f'width="{usable_w:.3f}" height="{usable_h:.3f}" />\n'
    )
    file.write('    </clipPath>\n')
    file.write('  </defs>\n')

    data_uri = f"data:image/png;base64,{png_data}"

    file.write(f'  <g clip-path="url(#{clip_id})">\n')
    file.write(
        f'    <image x="{x_img:.3f}" y="{y_img:.3f}" '
        f'width="{img_w:.3f}" height="{img_h:.3f}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'href="{data_uri}" '
        f'xlink:href="{data_uri}" />\n'
    )
    file.write('  </g>\n')

file.write('</svg>\n')
file.close()

print("Wrote gcode_file.svg")