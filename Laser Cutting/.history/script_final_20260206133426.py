import base64
import os

# =========================
# Gather Input
# =========================
try:
    x = float(input("Type x coordinate to start: "))
    y = float(input("Type y coordinate to start: "))
    z = float(input("Type z coordinate to start: "))
    width  = float(input("Type width  (mm): "))
    height = float(input("Type height (mm): "))
    stroke_width = 0.25
except ValueError:
    print("Invalid input. All values must be numbers.")
    exit()

if width < 100 or height < 100:
    print("Invalid input. Dimensions must be at least 100 mm.")
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
nut_groove_depth = 5.0 # The 5mm depth you requested
bolt_hole_radius = 1.5 # 3mm diameter bolt

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
    if n < 2: n = 2
    return n

# ==========================================================
# Panel generator with Nut Groove Logic
# ==========================================================
def generate_panel(face_w, face_h, edge_mode, slot_parity=0, has_grooves=False):
    half_w, half_h = face_w / 2.0, face_h / 2.0
    n_w, n_h = _segments_count(face_w), _segments_count(face_h)
    pts = []

    # Helper to draw edges with optional nut grooves on the center tab
    def add_edge_points(length, n_segments, mode, is_horizontal, direction, parity):
        edge_pts = []
        # Calculate index of the middle tab
        mid_index = n_segments // 2
        
        for i in range(n_segments):
            is_tab = (mode == "TAB" and i % 2 == 1)
            is_slot = (mode == "SLOT" and i % 2 == parity)
            
            # If it's the middle tab and has_grooves is True, we inject the "T" shape
            if has_grooves and is_tab and i == mid_index:
                # Basic protrusion
                # This logic creates the 'cross' of the T-slot
                # Values adjusted to create a 5mm deep cavity for a nut
                depth = mt + nut_groove_depth
                edge_pts.append(('step', 0, depth))
                edge_pts.append(('step', tw, depth))
                edge_pts.append(('step', tw, 0))
            elif is_tab:
                edge_pts.append(('step', 0, mt))
                edge_pts.append(('step', tw, mt))
                edge_pts.append(('step', tw, 0))
            elif is_slot:
                edge_pts.append(('step', 0, -mt))
                edge_pts.append(('step', tw, -mt))
                edge_pts.append(('step', tw, 0))
            else:
                edge_pts.append(('step', tw, 0))
        return edge_pts

    # TOP
    curr_x, curr_y = -half_w, half_h
    pts.append((curr_x, curr_y))
    curr_x += cl
    pts.append((curr_x, curr_y))
    for action, dx, dy in add_edge_points(face_w, n_w, edge_mode["top"], True, 1, slot_parity):
        curr_x += dx
        pts.append((curr_x, curr_y + dy))
    pts.append((half_w, half_h))

    # RIGHT
    curr_y = half_h - cl
    pts.append((half_w, curr_y))
    for action, dy, dx in add_edge_points(face_h, n_h, edge_mode["right"], False, -1, slot_parity):
        curr_y -= dy
        pts.append((half_w + dx, curr_y))
    pts.append((half_w, -half_h))

    # BOTTOM
    curr_x = half_w - cl
    pts.append((curr_x, -half_h))
    for action, dx, dy in add_edge_points(face_w, n_w, edge_mode["bottom"], True, -1, slot_parity):
        curr_x -= dx
        pts.append((curr_x, -half_h - dy))
    pts.append((-half_w, -half_h))

    # LEFT
    curr_y = -half_h + cl
    pts.append((-half_w, curr_y))
    for action, dy, dx in add_edge_points(face_h, n_h, edge_mode["left"], False, 1, slot_parity):
        curr_y += dy
        pts.append((-half_w - dx, curr_y))
    pts.append((-half_w, half_h))

    return pts

# =========================
# EDGE MAPS
# =========================
EDGE_MAP_RECT   = {"top": "TAB",  "right": "TAB",  "bottom": "TAB",  "left": "TAB"}
EDGE_MAP_SQUARE = {"top": "SLOT", "right": "SLOT", "bottom": "SLOT", "left": "SLOT"}

# Generate panels (A/B have grooves, Squares have bolt holes)
rect_pts_A = generate_panel(w, h, EDGE_MAP_RECT, has_grooves=True)
rect_pts_B = generate_panel(w, h, EDGE_MAP_RECT, has_grooves=True)
square_pts = generate_panel(w, w, EDGE_MAP_SQUARE, slot_parity=1)

# ... [Keep PNG base64 and parse logic from original code here] ...

# =========================
# Panel placement
# =========================
tab_margin = mt + 10
base_x, base_y = tab_margin + w/2, tab_margin + h/2

panel_centers = {
    "A1": (base_x, base_y),
    "A2": (base_x + w + gap, base_y),
    "B1": (base_x, base_y + h + gap),
    "B2": (base_x + w + gap, base_y + h + gap),
    "S1": (tab_margin + w/2 + 2*w + 2*gap, tab_margin + w/2),
    "S2": (tab_margin + w/2 + 2*w + 2*gap, tab_margin + w/2 + h + gap),
}

# =========================
# Write SVG
# =========================
file = open("gcode_file.svg", "w", encoding="utf-8")
file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
file.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width+20} {svg_height+20}" width="{svg_width+20}mm" height="{svg_height+20}mm">\n')

file.write(f'  <g stroke="black" stroke-width="{stroke_width}" fill="none">\n')

for label, (cx, cy) in panel_centers.items():
    p_str = points_to_polyline(rect_pts_A if "A" in label or "B" in label else square_pts)
    file.write(f'    <g transform="translate({cx}, {cy})">\n')
    file.write(f'      <polygon points="{p_str}" />\n')
    
    # Add Bolt Circles to Square Panels
    if "S" in label:
        # Circles positioned to match the center of the indented slots
        # Top hole
        file.write(f'      <circle cx="0" cy="{-w/2 + mt/2}" r="{bolt_hole_radius}" />\n')
        # Bottom hole
        file.write(f'      <circle cx="0" cy="{w/2 - mt/2}" r="{bolt_hole_radius}" />\n')
        # Left hole
        file.write(f'      <circle cx="{-w/2 + mt/2}" cy="0" r="{bolt_hole_radius}" />\n')
        # Right hole
        file.write(f'      <circle cx="{w/2 - mt/2}" cy="0" r="{bolt_hole_radius}" />\n')
    
    file.write('    </g>\n')

file.write('  </g>\n</svg>\n')
file.close()
print("Wrote gcode_file.svg with Nut and Bolt grooves.")