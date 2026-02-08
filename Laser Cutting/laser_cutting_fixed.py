#Vihaan Shah
#UNI: vvs2119
#MECE4606 Digital Manufacturing
#Laser Cutting Project - FIXED VERSION
#
# Generates 6 panels with finger joints that properly align and snap together
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
    length = float(input("Type length (mm): "))   # depth of box
    width  = float(input("Type width  (mm): "))   # width of box
    height = float(input("Type height (mm): "))   # height of box
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
d = length  # depth (using length input)
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
    edge_mode: dict with keys {"top","right","bottom","left"} each in {"TAB","SLOT","NONE"}
      TAB  => protrude outward on odd segments
      SLOT => indent inward on slot_parity segments
      NONE => straight edge (no tabs/slots)
    """
    half_w = face_w / 2.0
    half_h = face_h / 2.0

    n_w = _segments_count(face_w)
    n_h = _segments_count(face_h)

    pts = []

    # ---------- TOP edge ----------
    x0, y0 = -half_w,  half_h
    pts.append((x0, y0))
    
    if edge_mode["top"] == "NONE":
        pts.append((half_w, y0))
    else:
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
    x = half_w
    
    if edge_mode["right"] == "NONE":
        pts.append((x, -half_h))
    else:
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
    y = -half_h
    
    if edge_mode["bottom"] == "NONE":
        pts.append((-half_w, y))
    else:
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
    x = -half_w
    
    if edge_mode["left"] == "NONE":
        pts.append((x, half_h))
    else:
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
# EDGE MAPS FOR BOX ASSEMBLY
# Box structure:
# - Front/Back panels (w x h): tabs on left/right, slots on top/bottom
# - Left/Right side panels (d x h): tabs on top/bottom, slots on left/right  
# - Top/Bottom panels (w x d): all tabs
# =========================

# Front and Back panels (width x height)
EDGE_MAP_FRONT_BACK = {
    "top": "SLOT",     # receives tabs from top panel
    "right": "TAB",    # inserts into side panel
    "bottom": "SLOT",  # receives tabs from bottom panel
    "left": "TAB"      # inserts into side panel
}

# Left and Right side panels (depth x height)
EDGE_MAP_SIDES = {
    "top": "SLOT",     # receives tabs from top panel
    "right": "SLOT",   # receives tabs from front/back
    "bottom": "SLOT",  # receives tabs from bottom panel
    "left": "SLOT"     # receives tabs from front/back
}

# Top and Bottom panels (width x depth)
EDGE_MAP_TOP_BOTTOM = {
    "top": "TAB",      # inserts into back panel
    "right": "TAB",    # inserts into side panel
    "bottom": "TAB",   # inserts into front panel
    "left": "TAB"      # inserts into side panel
}

# =========================
# Generate panels
# =========================
# Panels for a box: Front, Back, Left, Right, Top, Bottom
# Layout: Front, Back in first row; Left, Right in second row; Top, Bottom in third position

front_pts = generate_panel(w, h, EDGE_MAP_FRONT_BACK, slot_parity=1)
back_pts = generate_panel(w, h, EDGE_MAP_FRONT_BACK, slot_parity=1)

left_pts = generate_panel(d, h, EDGE_MAP_SIDES, slot_parity=1)
right_pts = generate_panel(d, h, EDGE_MAP_SIDES, slot_parity=1)

top_pts = generate_panel(w, d, EDGE_MAP_TOP_BOTTOM, slot_parity=0)
bottom_pts = generate_panel(w, d, EDGE_MAP_TOP_BOTTOM, slot_parity=0)

front_str = points_to_polyline(front_pts)
back_str = points_to_polyline(back_pts)
left_str = points_to_polyline(left_pts)
right_str = points_to_polyline(right_pts)
top_str = points_to_polyline(top_pts)
bottom_str = points_to_polyline(bottom_pts)

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
        print("  FRONT = front panel")
        print("  BACK = back panel")
        print("  LEFT = left side panel")
        print("  RIGHT = right side panel")
        print("  TOP = top panel")
        print("  BOTTOM = bottom panel")

        art_target = input("Type one of: FRONT BACK LEFT RIGHT TOP BOTTOM: ").strip().upper()
        if art_target not in {"FRONT","BACK","LEFT","RIGHT","TOP","BOTTOM"}:
            print("Invalid panel choice. Skipping image.")
            png_data = None
            art_target = None

# =========================
# Ask for optional text engraving
# =========================
add_text = input("Add engravable text onto one face? (y/n): ").strip().lower()

text_content = None
text_target = None
text_font_size = 12.0

def calculate_auto_font_size(text, panel_width, panel_height):
    """
    Calculate font size to fit text within panel with margin.
    Assumes average character width is ~0.6 * font_size for sans-serif.
    """
    text_margin = 20.0  # mm margin on each side
    usable_width = panel_width - 2 * text_margin
    usable_height = panel_height - 2 * text_margin
    
    if len(text) == 0:
        return 12.0
    
    # Estimate: character width ≈ 0.6 * font_size for most sans-serif fonts
    # Text width ≈ len(text) * 0.6 * font_size
    # Solve for font_size: font_size = usable_width / (len(text) * 0.6)
    font_size_by_width = usable_width / (len(text) * 0.6)
    
    # Limit by height (font height ≈ font_size)
    font_size_by_height = usable_height * 0.5  # Use 50% of height for comfort
    
    # Take the smaller of the two constraints
    auto_size = min(font_size_by_width, font_size_by_height)
    
    # Clamp between reasonable bounds
    auto_size = max(4.0, min(auto_size, 50.0))
    
    return auto_size

if add_text == "y":
    text_content = input("Enter text to engrave: ").strip()
    
    if text_content:
        print("Choose which panel to place text on:")
        print("  FRONT = front panel")
        print("  BACK = back panel")
        print("  LEFT = left side panel")
        print("  RIGHT = right side panel")
        print("  TOP = top panel")
        print("  BOTTOM = bottom panel")
        
        text_target = input("Type one of: FRONT BACK LEFT RIGHT TOP BOTTOM: ").strip().upper()
        if text_target not in {"FRONT","BACK","LEFT","RIGHT","TOP","BOTTOM"}:
            print("Invalid panel choice. Skipping text.")
            text_content = None
            text_target = None
        else:
            # Determine panel dimensions for auto-scaling
            if text_target in {"FRONT", "BACK"}:
                panel_w_for_text = w
                panel_h_for_text = h
            elif text_target in {"LEFT", "RIGHT"}:
                panel_w_for_text = d
                panel_h_for_text = h
            else:  # TOP or BOTTOM
                panel_w_for_text = w
                panel_h_for_text = d
            
            # Calculate auto font size
            text_font_size = calculate_auto_font_size(text_content, panel_w_for_text, panel_h_for_text)
            
            print(f"Auto-calculated font size: {text_font_size:.1f}mm")
            override = input("Press Enter to accept, or type a custom size (mm): ").strip()
            if override:
                try:
                    custom_size = float(override)
                    if custom_size > 0:
                        text_font_size = custom_size
                except:
                    pass  # Keep auto size
    else:
        print("No text entered. Skipping text.")

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
    "FRONT": (base_x, base_y),
    "BACK": (base_x + w + gap, base_y),
    "LEFT": (base_x, base_y + h + gap),
    "RIGHT": (base_x + w + gap, base_y + h + gap),
    "TOP": (tab_margin + w/2 + 2*w + 2*gap, tab_margin + d/2),
    "BOTTOM": (tab_margin + w/2 + 2*w + 2*gap, tab_margin + d/2 + h + gap),
}

panel_sizes = {
    "FRONT": (w, h),
    "BACK": (w, h),
    "LEFT": (d, h),
    "RIGHT": (d, h),
    "TOP": (w, d),
    "BOTTOM": (w, d),
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

# FRONT panel
file.write(f'    <g transform="translate({panel_centers["FRONT"][0]}, {panel_centers["FRONT"][1]})">\n')
file.write(f'      <polygon points="{front_str}" />\n')
file.write('    </g>\n')

# BACK panel
file.write(f'    <g transform="translate({panel_centers["BACK"][0]}, {panel_centers["BACK"][1]})">\n')
file.write(f'      <polygon points="{back_str}" />\n')
file.write('    </g>\n')

# LEFT panel
file.write(f'    <g transform="translate({panel_centers["LEFT"][0]}, {panel_centers["LEFT"][1]})">\n')
file.write(f'      <polygon points="{left_str}" />\n')
file.write('    </g>\n')

# RIGHT panel
file.write(f'    <g transform="translate({panel_centers["RIGHT"][0]}, {panel_centers["RIGHT"][1]})">\n')
file.write(f'      <polygon points="{right_str}" />\n')
file.write('    </g>\n')

# TOP panel
file.write(f'    <g transform="translate({panel_centers["TOP"][0]}, {panel_centers["TOP"][1]})">\n')
file.write(f'      <polygon points="{top_str}" />\n')
file.write('    </g>\n')

# BOTTOM panel
file.write(f'    <g transform="translate({panel_centers["BOTTOM"][0]}, {panel_centers["BOTTOM"][1]})">\n')
file.write(f'      <polygon points="{bottom_str}" />\n')
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

# ---- Text engraving (centered on panel) ----
if text_content is not None and text_target is not None:
    tx, ty = panel_centers[text_target]
    
    # SVG text is positioned at baseline, so we center it at panel center
    # Use text-anchor="middle" and dominant-baseline="middle" for centering
    file.write(f'  <g stroke="blue" stroke-width="0.1" fill="blue">\n')
    file.write(
        f'    <text x="{tx:.3f}" y="{ty:.3f}" '
        f'font-family="Arial, sans-serif" '
        f'font-size="{text_font_size:.1f}" '
        f'text-anchor="middle" '
        f'dominant-baseline="middle">'
    )
    # Escape special XML characters
    escaped_text = text_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    file.write(escaped_text)
    file.write('</text>\n')
    file.write('  </g>\n')

file.write('</svg>\n')
file.close()

print("\n" + "="*60)
print("BOX ASSEMBLY GUIDE:")
print("="*60)
print("Panel Layout:")
print("  Row 1: FRONT (left), BACK (middle)")
print("  Row 2: LEFT (left), RIGHT (middle)")  
print("  Row 3: TOP (right-top), BOTTOM (right-bottom)")
print("\nAssembly:")
print("1. FRONT/BACK panels have tabs on left/right edges")
print("2. LEFT/RIGHT side panels have slots on all edges")
print("3. TOP/BOTTOM panels have tabs on all edges")
print("4. Tabs insert into matching slots to form a box")
print("\nEngraving:")
print("  Red lines = cut paths (panels)")
if png_data is not None:
    print(f"  Embedded image = raster engrave on {art_target} panel")
if text_content is not None:
    print(f"  Blue text = vector engrave on {text_target} panel")
print("="*60)
print(f"\nWrote gcode_file.svg")
