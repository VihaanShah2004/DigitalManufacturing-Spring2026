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

def _segments_count(edge_len):
    tab_section = edge_len - cl - cr
    n = int(round(tab_section / tw))
    if n < 2:
        n = 2
    return n

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
# SVG import helpers
# =========================
def read_svg_inner(svg_path):
    """
    Reads an SVG file and returns (inner_markup, viewbox_tuple_or_None)
    viewbox_tuple: (minx, miny, vbw, vbh)
    """
    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            s = f.read()
    except Exception as e:
        print(f"Could not read SVG file: {e}")
        return None, None

    lower = s.lower()
    i0 = lower.find("<svg")
    if i0 == -1:
        print("That file doesn't contain <svg ...>")
        return None, None

    i1 = lower.find(">", i0)
    if i1 == -1:
        print("SVG header seems malformed.")
        return None, None

    # try parse viewBox="minx miny w h"
    header = s[i0:i1+1]
    hlow = header.lower()
    vb = None
    vb_key = 'viewbox="'
    k = hlow.find(vb_key)
    if k != -1:
        k += len(vb_key)
        k2 = hlow.find('"', k)
        if k2 != -1:
            vb_str = header[k:k2].strip()
            parts = vb_str.replace(",", " ").split()
            if len(parts) == 4:
                try:
                    vb = (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
                except:
                    vb = None

    # inner content between <svg ...> and </svg>
    end = lower.rfind("</svg>")
    if end == -1:
        print("SVG missing </svg>")
        return None, None

    inner = s[i1+1:end]
    return inner.strip(), vb

# =========================
# EDGE MAPS
# =========================
EDGE_MAP_RECT = {"top": "TAB", "right": "TAB", "bottom": "TAB", "left": "TAB"}
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
# Ask for optional SVG artwork
# =========================
add_art = input("Add an SVG image onto one face? (y/n): ").strip().lower()
art_inner = None
art_vb = None
art_target = None
art_margin = 10.0  # mm margin from edges inside the panel
art_stroke_black = True  # makes artwork black fill/stroke (good for engraving)

if add_art == "y":
    svg_path = input("Enter path to SVG file (e.g., logo.svg): ").strip()
    inner, vb = read_svg_inner(svg_path)
    if inner is None:
        print("Skipping artwork (could not read/parse SVG).")
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
            print("Invalid panel choice, skipping artwork.")
            art_target = None
        else:
            art_inner = inner
            art_vb = vb

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

# centers for the 6 pieces
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
file.write(f'viewBox="0 0 {view_w} {view_h}" width="{view_w}mm" height="{view_h}mm">\n')

# ---- CUT LINES group (red) ----
file.write(f'  <g stroke="red" stroke-width="{stroke_width}" fill="none">\n')

# 4 side panels
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

# square panels
file.write(f'    <g transform="translate({panel_centers["S1"][0]}, {panel_centers["S1"][1]})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({panel_centers["S2"][0]}, {panel_centers["S2"][1]})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write('  </g>\n')  # end cut group

# ---- ARTWORK group (black) ----
if art_inner is not None and art_target is not None:
    cx, cy = panel_centers[art_target]
    pw, ph = panel_sizes[art_target]

    # usable area inside the panel
    usable_w = max(1.0, pw - 2*art_margin)
    usable_h = max(1.0, ph - 2*art_margin)

    # determine viewBox for scaling
    # if missing, assume 0 0 100 100
    if art_vb is None:
        vb_minx, vb_miny, vb_w, vb_h = 0.0, 0.0, 100.0, 100.0
    else:
        vb_minx, vb_miny, vb_w, vb_h = art_vb

    # scale to fit (preserve aspect)
    sx = usable_w / vb_w
    sy = usable_h / vb_h
    s = sx if sx < sy else sy

    # center inside the panel
    art_x = cx - (vb_w * s)/2.0
    art_y = cy - (vb_h * s)/2.0

    # translate so the SVG viewBox origin maps correctly
    # final: translate(panel-center-fit) * scale * translate(-vb_minx, -vb_miny)
    file.write('  <g ')
    if art_stroke_black:
        file.write('stroke="#000000" fill="none" stroke-width="0.25" ')
    file.write('>\n')
    file.write(f'    <g transform="translate({art_x:.3f},{art_y:.3f}) scale({s:.6f}) translate({-vb_minx:.3f},{-vb_miny:.3f})">\n')
    file.write(art_inner + "\n")
    file.write('    </g>\n')
    file.write('  </g>\n')

file.write('</svg>\n')
file.close()

print("Wrote gcode_file.svg")