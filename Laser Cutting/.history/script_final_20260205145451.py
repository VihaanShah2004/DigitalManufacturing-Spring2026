#Vihaan Shah
#UNI: vvs2119
#MECE4606 Digital Manufacturing
#Laser Cutting Project

#Gather Input
try:
    x = float(input("Type x coordinate to start: "))
    y = float(input("Type y coordinate to start: "))
    z = float(input("Type z coordinate to start: "))
    length = float(input("Type length to start (mm): "))
    width = float(input("Type width to start (mm): "))
    height = float(input("Type height to start (mm): "))
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

w = width
h = height
gap = 100
svg_width = 3 * w + 2 * gap
svg_height = 2 * h + gap

# Material and tab parameters from SVG analysis
material_thickness = 3.0   # 3mm material thickness
tab_width = 9.0            # 9mm tabs
corner_left = 6.5          # Left corner offset
corner_right = 12.5        # Right corner offset
mt = material_thickness
tw = tab_width
cl = corner_left
cr = corner_right

def points_to_polyline(points):
    return " ".join(f"{px:.3f},{py:.3f}" for px, py in points)

# -----------------------------
# FIXED: Square panel generator
# Uses BOTH cl and cr so pattern aligns and ends correctly.
# Pattern: SLOT IN on even segments (i=0,2,4,...)
# -----------------------------
def generate_square_panel(size):
    half = size / 2
    points = []

    tab_section = size - cl - cr
    num_segments = int(round(tab_section / tw))

    # TOP edge: left -> right (slot-in goes downward: y - mt)
    x, y = -half, half
    points.append((x, y))

    x = -half + cl
    points.append((x, y))

    for i in range(num_segments):
        if i % 2 == 0:  # EVEN = SLOT IN
            points.append((x, y - mt))
            x += tw
            points.append((x, y - mt))
            points.append((x, y))
        else:
            x += tw
            points.append((x, y))

    # End of finger section, then final corner segment cr
    x = half - cr
    points.append((x, y))
    x = half
    points.append((x, y))

    # RIGHT edge: top -> bottom (slot-in goes left: x - mt)
    y = half - cl
    points.append((x, y))

    for i in range(num_segments):
        if i % 2 == 0:  # EVEN = SLOT IN
            points.append((x - mt, y))
            y -= tw
            points.append((x - mt, y))
            points.append((x, y))
        else:
            y -= tw
            points.append((x, y))

    y = -half + cr
    points.append((x, y))
    y = -half
    points.append((x, y))

    # BOTTOM edge: right -> left (slot-in goes upward: y + mt)
    x = half - cl
    points.append((x, y))

    for i in range(num_segments):
        if i % 2 == 0:  # EVEN = SLOT IN
            points.append((x, y + mt))
            x -= tw
            points.append((x, y + mt))
            points.append((x, y))
        else:
            x -= tw
            points.append((x, y))

    x = -half + cr
    points.append((x, y))
    x = -half
    points.append((x, y))

    # LEFT edge: bottom -> top (slot-in goes right: x + mt)
    y = -half + cl
    points.append((x, y))

    for i in range(num_segments):
        if i % 2 == 0:  # EVEN = SLOT IN
            points.append((x + mt, y))
            y += tw
            points.append((x + mt, y))
            points.append((x, y))
        else:
            y += tw
            points.append((x, y))

    y = half - cr
    points.append((x, y))
    y = half
    points.append((x, y))

    return points

# -----------------------------
# FIXED: Rect panel generator
# Uses BOTH cl and cr so pattern aligns.
# IMPORTANT CHANGE: TAB OUT on EVEN segments to complement square (which is slot-in on even).
# -----------------------------
def generate_rect_panel(width, height):
    half_w = width / 2
    half_h = height / 2
    points = []

    tab_section_w = width - cl - cr
    tab_section_h = height - cl - cr
    num_segments_w = int(round(tab_section_w / tw))
    num_segments_h = int(round(tab_section_h / tw))

    # TOP edge: left -> right (tab-out goes up: y + mt)
    x, y = -half_w, half_h
    points.append((x, y))

    x = -half_w + cl
    points.append((x, y))

    for i in range(num_segments_w):
        if i % 2 == 0:  # EVEN = TAB OUT  (complements square)
            points.append((x, y + mt))
            x += tw
            points.append((x, y + mt))
            points.append((x, y))
        else:
            x += tw
            points.append((x, y))

    x = half_w - cr
    points.append((x, y))
    x = half_w
    points.append((x, y))

    # RIGHT edge: top -> bottom (tab-out goes right: x + mt)
    y = half_h - cl
    points.append((x, y))

    for i in range(num_segments_h):
        if i % 2 == 0:  # EVEN = TAB OUT
            points.append((x + mt, y))
            y -= tw
            points.append((x + mt, y))
            points.append((x, y))
        else:
            y -= tw
            points.append((x, y))

    y = -half_h + cr
    points.append((x, y))
    y = -half_h
    points.append((x, y))

    # BOTTOM edge: right -> left (tab-out goes down: y - mt)
    x = half_w - cl
    points.append((x, y))

    for i in range(num_segments_w):
        if i % 2 == 0:  # EVEN = TAB OUT
            points.append((x, y - mt))
            x -= tw
            points.append((x, y - mt))
            points.append((x, y))
        else:
            x -= tw
            points.append((x, y))

    x = -half_w + cr
    points.append((x, y))
    x = -half_w
    points.append((x, y))

    # LEFT edge: bottom -> top (tab-out goes left: x - mt)
    y = -half_h + cl
    points.append((x, y))

    for i in range(num_segments_h):
        if i % 2 == 0:  # EVEN = TAB OUT
            points.append((x - mt, y))
            y += tw
            points.append((x - mt, y))
            points.append((x, y))
        else:
            y += tw
            points.append((x, y))

    y = half_h - cr
    points.append((x, y))
    y = half_h
    points.append((x, y))

    return points

# Generate panels
square_pts = generate_square_panel(w)
rect_pts = generate_rect_panel(w, h)

# Calculate proper margins to account for tabs sticking out
tab_margin = mt + 5
total_w = svg_width + 2 * tab_margin
total_h = svg_height + 2 * tab_margin
view_w = total_w
view_h = total_h

#Write SVG File (ONLY file.write)
file = open("gcode_file.svg", "w")
file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" ')
file.write(f'viewBox="0 0 {view_w:.3f} {view_h:.3f}" width="{view_w:.2f}mm" height="{view_h:.2f}mm">\n')
file.write(f'  <g stroke="red" stroke-width="{stroke_width}" fill="none">\n')

rect_points_str = points_to_polyline(rect_pts)
square_points_str = points_to_polyline(square_pts)

# Calculate base offsets to center panels properly
base_x = tab_margin + w/2
base_y = tab_margin + h/2

# Row 1: 2 rectangular panels (top left + top middle)
file.write(f'    <g transform="translate({base_x:.3f}, {base_y:.3f})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({(base_x + w + gap):.3f}, {base_y:.3f})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

# Row 2: 2 more rectangular panels (bottom left + bottom middle)
file.write(f'    <g transform="translate({base_x:.3f}, {(base_y + h + gap):.3f})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({(base_x + w + gap):.3f}, {(base_y + h + gap):.3f})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

# Square panels on the right column
square_base_x = tab_margin + w/2

file.write(f'    <g transform="translate({(square_base_x + 2*w + 2*gap):.3f}, {(tab_margin + w/2):.3f})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({(square_base_x + 2*w + 2*gap):.3f}, {(tab_margin + w/2 + h + gap):.3f})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write('  </g>\n')
file.write('</svg>\n')
file.close()

print("Wrote gcode_file.svg")