#Vihaan Shah
#UNI: vvs2119
#MECE4606 Digital Manufacturing
#Laser Cutting Project

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

def _segments_count(edge_len, force_even=False):
    tab_section = edge_len - cl - cr
    n = int(round(tab_section / tw))

    # keep sane minimum
    if n < 2:
        n = 2

    # IMPORTANT FIX:
    # For squares: force EVEN so SLOT-even doesn’t produce 1 extra feature (e.g., 9->5 vs 4).
    if force_even and (n % 2 == 1):
        n -= 1
        if n < 2:
            n = 2

    return n

# ==========================================================
# Panel generator with per-edge TAB/SLOT control
# ==========================================================
def generate_panel(face_w, face_h, edge_mode, force_even_segments=False):
    """
    edge_mode: dict with keys {"top","right","bottom","left"} each in {"TAB","SLOT"}
      TAB  => protrude outward on odd segments
      SLOT => indent inward on even segments
    force_even_segments: if True, force even segment count on both axes
    """
    half_w = face_w / 2.0
    half_h = face_h / 2.0

    n_w = _segments_count(face_w, force_even=force_even_segments)
    n_h = _segments_count(face_h, force_even=force_even_segments)

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
            if i % 2 == 0:
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
            if i % 2 == 0:
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
            if i % 2 == 0:
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
            if i % 2 == 0:
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
EDGE_MAP_RECT = {"top": "TAB", "right": "TAB", "bottom": "TAB", "left": "TAB"}
EDGE_MAP_RECT_FIX = {"top": "TAB", "right": "TAB", "bottom": "TAB", "left": "TAB"}

EDGE_MAP_SQUARE_FIX = {"top": "SLOT", "right": "SLOT", "bottom": "SLOT", "left": "SLOT"}

# =========================
# Generate panels
# =========================
rect_pts_A = generate_panel(w, h, EDGE_MAP_RECT, force_even_segments=False)
rect_pts_B = generate_panel(w, h, EDGE_MAP_RECT_FIX, force_even_segments=False)

# ✅ IMPORTANT: force_even_segments=True ONLY for squares
square_pts = generate_panel(w, w, EDGE_MAP_SQUARE_FIX, force_even_segments=True)

rect_points_str_A = points_to_polyline(rect_pts_A)
rect_points_str_B = points_to_polyline(rect_pts_B)
square_points_str = points_to_polyline(square_pts)

# =========================
# SVG sizing and margins
# =========================
tab_margin = mt + 5
total_w = svg_width + 2 * tab_margin
total_h = svg_height + 2 * tab_margin
view_w = total_w
view_h = total_h

# =========================
# Write SVG (ONLY file.write)
# =========================
file = open("gcode_file.svg", "w", encoding="utf-8")
file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" ')
file.write(f'viewBox="0 0 {view_w} {view_h}" width="{view_w}mm" height="{view_h}mm">\n')
file.write(f'  <g stroke="red" stroke-width="{stroke_width}" fill="none">\n')

base_x = tab_margin + w / 2
base_y = tab_margin + h / 2

# 4 side panels
file.write(f'    <g transform="translate({base_x}, {base_y})">\n')
file.write(f'      <polygon points="{rect_points_str_A}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({base_x + w + gap}, {base_y})">\n')
file.write(f'      <polygon points="{rect_points_str_B}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({base_x}, {base_y + h + gap})">\n')
file.write(f'      <polygon points="{rect_points_str_B}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({base_x + w + gap}, {base_y + h + gap})">\n')
file.write(f'      <polygon points="{rect_points_str_A}" />\n')
file.write('    </g>\n')

# 2 square panels on the right
square_base_x = tab_margin + w / 2

file.write(f'    <g transform="translate({square_base_x + 2*w + 2*gap}, {tab_margin + w/2})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({square_base_x + 2*w + 2*gap}, {tab_margin + w/2 + h + gap})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write('  </g>\n')
file.write('</svg>\n')
file.close()

print("Wrote gcode_file.svg")