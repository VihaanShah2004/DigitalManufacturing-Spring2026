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
corner_left = 6.5        # Left corner offset
corner_right = 12.5       # Right corner offset  
mt = material_thickness
tw = tab_width
cl = corner_left
cr = corner_right

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
    """Generate square panel - SLOTS IN on even segments (0,2,4,6,8) - OPPOSITE of rectangles"""
    half = size / 2
    points = []
    
    # Calculate: 100mm - 6.5mm - 12.5mm = 81mm / 9mm = 9 segments
    tab_section = size - cl - cr
    num_segments = int(round(tab_section / tw))
    
    # Top edge: Pattern is SLOT, normal, SLOT, normal, SLOT, normal, SLOT, normal, SLOT (5 slots in)
    x, y = -half, half
    points.append((x, y))
    x = -half + cl
    points.append((x, y))
    
    for i in range(num_segments):
        if i % 2 == 0:  # Even = SLOT IN (complementary to rectangles)
            points.append((x, y - mt))
            x += tw
            points.append((x, y - mt))
            points.append((x, y))
        else:  # Odd = normal
            x += tw
            points.append((x, y))
    
    x = half
    points.append((x, y))
    
    # Right edge: Same pattern
    y = half - cl
    points.append((x, y))
    
    for i in range(num_segments):
        if i % 2 == 0:  # SLOT IN
            points.append((x - mt, y))
            y -= tw
            points.append((x - mt, y))
            points.append((x, y))
        else:  # Normal
            y -= tw
            points.append((x, y))
    
    y = -half
    points.append((x, y))
    
    # Bottom edge: Same pattern
    x = half - cl
    points.append((x, y))
    
    for i in range(num_segments):
        if i % 2 == 0:  # SLOT IN
            points.append((x, y + mt))
            x -= tw
            points.append((x, y + mt))
            points.append((x, y))
        else:  # Normal
            x -= tw
            points.append((x, y))
    
    x = -half
    points.append((x, y))
    
    # Left edge: Same pattern
    y = -half + cl
    points.append((x, y))
    
    for i in range(num_segments):
        if i % 2 == 0:  # SLOT IN
            points.append((x + mt, y))
            y += tw
            points.append((x + mt, y))
            points.append((x, y))
        else:  # Normal
            y += tw
            points.append((x, y))
    
    y = half
    points.append((x, y))
    
    return points

# Generate rectangular panel points (for side panels)
def generate_rect_panel(width, height):
    """Generate a rectangular panel with uniform tab/slot pattern"""
    half_w = width / 2
    half_h = height / 2
    points = []
    
    # Calculate: 100mm - 6.5mm - 12.5mm = 81mm / 9mm = 9 segments
    tab_section_w = width - cl - cr
    tab_section_h = height - cl - cr
    num_segments_w = int(round(tab_section_w / tw))
    num_segments_h = int(round(tab_section_h / tw))
    
    # Top edge: Pattern is normal, TAB, normal, TAB, normal, TAB, normal, TAB, normal (4 tabs out)
    x, y = -half_w, half_h
    points.append((x, y))
    x = -half_w + cl
    points.append((x, y))
    
    for i in range(num_segments_w):
        if i % 2 == 1:  # Odd = TAB OUT
            points.append((x, y + mt))
            x += tw
            points.append((x, y + mt))
            points.append((x, y))
        else:  # Even = normal
            x += tw
            points.append((x, y))
    
    x = half_w
    points.append((x, y))
    
    # Right edge: Same pattern
    y = half_h - cl
    points.append((x, y))
    
    for i in range(num_segments_h):
        if i % 2 == 1:  # TAB OUT
            points.append((x + mt, y))
            y -= tw
            points.append((x + mt, y))
            points.append((x, y))
        else:  # Normal
            y -= tw
            points.append((x, y))
    
    y = -half_h
    points.append((x, y))
    
    # Bottom edge: Same pattern
    x = half_w - cl
    points.append((x, y))
    
    for i in range(num_segments_w):
        if i % 2 == 1:  # TAB OUT
            points.append((x, y - mt))
            x -= tw
            points.append((x, y - mt))
            points.append((x, y))
        else:  # Normal
            x -= tw
            points.append((x, y))
    
    x = -half_w
    points.append((x, y))
    
    # Left edge: Same pattern  
    y = -half_h + cl
    points.append((x, y))
    
    for i in range(num_segments_h):
        if i % 2 == 1:  # TAB OUT
            points.append((x - mt, y))
            y += tw
            points.append((x - mt, y))
            points.append((x, y))
        else:  # Normal
            y += tw
            points.append((x, y))
    
    y = half_h
    points.append((x, y))
    
    return points

def points_to_polyline(points):
    return " ".join(f"{px},{py}" for px, py in points)

# Generate panels
square_pts = generate_square_panel(w)
rect_pts = generate_rect_panel(w, h)

# No holes needed for this design

# Calculate proper margins to account for tabs sticking out
tab_margin = mt + 5
total_w = svg_width + 2 * tab_margin
total_h = svg_height + 2 * tab_margin
view_w = total_w
view_h = total_h

#Write SVG File
file = open("gcode_file.svg", "w")
file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" ')
file.write(f'viewBox="0 0 {view_w} {view_h}" width="{view_w}mm" height="{view_h}mm">\n')
file.write(f'  <g stroke="red" stroke-width="{stroke_width}" fill="none">\n')

rect_points_str = points_to_polyline(rect_pts)
square_points_str = points_to_polyline(square_pts)

# Calculate base offsets to center panels properly
base_x = tab_margin + w/2
base_y = tab_margin + h/2

# Row 1: 4 rectangular panels
file.write(f'    <g transform="translate({base_x}, {base_y})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({base_x + w + gap}, {base_y})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

# Row 2: 2 more rectangular panels
file.write(f'    <g transform="translate({base_x}, {base_y + h + gap})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({base_x + w + gap}, {base_y + h + gap})">\n')
file.write(f'      <polygon points="{rect_points_str}" />\n')
file.write('    </g>\n')

# Square panels (same size as width, so use w/2 offset)
square_base_x = tab_margin + w/2

file.write(f'    <g transform="translate({square_base_x + 2*w + 2*gap}, {tab_margin + w/2})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write(f'    <g transform="translate({square_base_x + 2*w + 2*gap}, {tab_margin + w/2 + h + gap})">\n')
file.write(f'      <polygon points="{square_points_str}" />\n')
file.write('    </g>\n')

file.write('  </g>\n')
file.write('</svg>\n')
file.close()
