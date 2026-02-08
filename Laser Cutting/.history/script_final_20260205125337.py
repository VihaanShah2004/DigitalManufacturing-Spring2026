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
tab_width = 9.0           # 9mm tabs
mt = material_thickness
tw = tab_width

# Calculate number of tabs that fit on each edge
def create_edge_with_tabs(start_pos, edge_length, is_horizontal, tabs_outward):
    """
    Create edge with alternating tabs and slots
    start_pos: (x, y) starting position
    edge_length: total length of the edge
    is_horizontal: True if edge runs left-right, False if up-down
    tabs_outward: True if tabs stick out, False if tabs go inward (slots)
    """
    points = []
    x, y = start_pos
    
    # Calculate how many tab/slot pairs fit
    num_tabs = int(edge_length / tw)
    remaining = edge_length - (num_tabs * tw)
    start_offset = remaining / 2  # Center the tab pattern
    
    current_pos = 0
    tab_out = tabs_outward
    
    while current_pos < edge_length:
        segment_length = tw if current_pos + tw <= edge_length else edge_length - current_pos
        
        if is_horizontal:
            # Moving along X axis
            if current_pos == 0:
                points.append((x, y))
            
            x += segment_length
            points.append((x, y))
            
            if tab_out and current_pos + segment_length < edge_length:
                y -= mt
                points.append((x, y))
            elif not tab_out and current_pos + segment_length < edge_length:
                y += mt
                points.append((x, y))
        else:
            # Moving along Y axis
            if current_pos == 0:
                points.append((x, y))
            
            y += segment_length
            points.append((x, y))
            
            if tab_out and current_pos + segment_length < edge_length:
                x += mt
                points.append((x, y))
            elif not tab_out and current_pos + segment_length < edge_length:
                x -= mt
                points.append((x, y))
        
        current_pos += segment_length
        tab_out = not tab_out
    
    return points

# Generate square panel points (for top/bottom panels)
def generate_square_panel(size):
    """Generate a square panel with uniform tab/slot pattern on all edges"""
    half = size / 2
    points = []
    
    # Top edge (left to right) - tabs outward
    x, y = -half, half
    for i in range(int(size / tw)):
        if i * tw < size:
            seg_len = min(tw, size - i * tw)
            if i % 2 == 1:  # Tab out
                points.append((x, y))
                points.append((x, y + mt))
                x += seg_len
                points.append((x, y + mt))
                points.append((x, y))
            else:  # Normal edge
                x += seg_len
                points.append((x, y))
    
    # Right edge (top to bottom) - tabs outward  
    x, y = half, half
    for i in range(int(size / tw)):
        if i * tw < size:
            seg_len = min(tw, size - i * tw)
            if i % 2 == 1:  # Tab out
                points.append((x, y))
                points.append((x + mt, y))
                y -= seg_len
                points.append((x + mt, y))
                points.append((x, y))
            else:  # Normal edge
                y -= seg_len
                points.append((x, y))
    
    # Bottom edge (right to left) - tabs outward
    x, y = half, -half
    for i in range(int(size / tw)):
        if i * tw < size:
            seg_len = min(tw, size - i * tw)
            if i % 2 == 1:  # Tab out
                points.append((x, y))
                points.append((x, y - mt))
                x -= seg_len
                points.append((x, y - mt))
                points.append((x, y))
            else:  # Normal edge
                x -= seg_len
                points.append((x, y))
    
    # Left edge (bottom to top) - tabs outward
    x, y = -half, -half
    for i in range(int(size / tw)):
        if i * tw < size:
            seg_len = min(tw, size - i * tw)
            if i % 2 == 1:  # Tab out
                points.append((x, y))
                points.append((x - mt, y))
                y += seg_len
                points.append((x - mt, y))
                points.append((x, y))
            else:  # Normal edge
                y += seg_len
                points.append((x, y))
    
    return points

# Generate rectangular panel points (for side panels)
def generate_rect_panel(width, height):
    """Generate a rectangular panel with uniform tab/slot pattern"""
    half_w = width / 2
    half_h = height / 2
    points = []
    
    # Top edge
    x, y = -half_w, half_h
    for i in range(int(width / tw)):
        if i * tw < width:
            seg_len = min(tw, width - i * tw)
            if i % 2 == 1:
                points.append((x, y))
                points.append((x, y + mt))
                x += seg_len
                points.append((x, y + mt))
                points.append((x, y))
            else:
                x += seg_len
                points.append((x, y))
    
    # Right edge
    x, y = half_w, half_h
    for i in range(int(height / tw)):
        if i * tw < height:
            seg_len = min(tw, height - i * tw)
            if i % 2 == 1:
                points.append((x, y))
                points.append((x + mt, y))
                y -= seg_len
                points.append((x + mt, y))
                points.append((x, y))
            else:
                y -= seg_len
                points.append((x, y))
    
    # Bottom edge
    x, y = half_w, -half_h
    for i in range(int(width / tw)):
        if i * tw < width:
            seg_len = min(tw, width - i * tw)
            if i % 2 == 1:
                points.append((x, y))
                points.append((x, y - mt))
                x -= seg_len
                points.append((x, y - mt))
                points.append((x, y))
            else:
                x -= seg_len
                points.append((x, y))
    
    # Left edge
    x, y = -half_w, -half_h
    for i in range(int(height / tw)):
        if i * tw < height:
            seg_len = min(tw, height - i * tw)
            if i % 2 == 1:
                points.append((x, y))
                points.append((x - mt, y))
                y += seg_len
                points.append((x - mt, y))
                points.append((x, y))
            else:
                y += seg_len
                points.append((x, y))
    
    return points

def points_to_polyline(points):
    return " ".join(f"{px},{py}" for px, py in points)

# Generate panels
square_pts = generate_square_panel(w)
rect_pts = generate_rect_panel(w, h)

# Bolt holes for square panels - positioned at the center of tabs
circle_radius = 3.35  # 2-56 nut clearance
hole_top = (0, w/2 + mt/2)
hole_right = (w/2 + mt/2, 0)
hole_bottom = (0, -(w/2 + mt/2))
hole_left = (-(w/2 + mt/2), 0)

total_w = max(svg_width, x + svg_width)
total_h = max(svg_height, y + svg_height)
margin = 10
view_w = total_w + 2 * margin
view_h = total_h + 2 * margin

#Write SVG File
file = open("gcode_file.svg", "w")
file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" ')
file.write(f'viewBox="-{margin} -{margin} {view_w} {view_h}" width="{view_w}mm" height="{view_h}mm">\n')
file.write(f'  <g transform="translate({x + margin}, {y + margin})" stroke="red" stroke-width="{stroke_width}" fill="none">\n')

rect_points_str = points_to_polyline(rect_pts)
square_points_str = points_to_polyline(square_pts)

# Row 1: 4 rectangular panels
file.write('    <g transform="translate(0, 0)">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({w + gap}, 0)">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate(0, {h + gap})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({w + gap}, {h + gap})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({2*w + 2*gap}, 0)">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write(f'      <circle cx="{hole_top[0]}" cy="{hole_top[1]}" r="{circle_radius}" />\n')
file.write(f'      <circle cx="{hole_right[0]}" cy="{hole_right[1]}" r="{circle_radius}" />\n')
file.write(f'      <circle cx="{hole_bottom[0]}" cy="{hole_bottom[1]}" r="{circle_radius}" />\n')
file.write(f'      <circle cx="{hole_left[0]}" cy="{hole_left[1]}" r="{circle_radius}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({2*w + 2*gap}, {h + gap})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write(f'      <circle cx="{hole_top[0]}" cy="{hole_top[1]}" r="{circle_radius}" />\n')
file.write(f'      <circle cx="{hole_right[0]}" cy="{hole_right[1]}" r="{circle_radius}" />\n')
file.write(f'      <circle cx="{hole_bottom[0]}" cy="{hole_bottom[1]}" r="{circle_radius}" />\n')
file.write(f'      <circle cx="{hole_left[0]}" cy="{hole_left[1]}" r="{circle_radius}" />\n')
file.write('    </g>\n')

file.write('  </g>\n')
file.write('</svg>\n')
file.close()
