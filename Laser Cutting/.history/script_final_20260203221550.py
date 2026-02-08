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
    stroke_width = float(input("Type stroke width to start: "))
except ValueError:
    print("Invalid input. All values must be numbers.")
    exit()

if width < 500 or height < 500 or length < 500:
    print("Invalid input. Length, width, and height must be at least 500 mm.")
    exit()
if stroke_width <= 0:
    print("Invalid input. Stroke width must be greater than 0.")
    exit()

w = width
h = height
gap = 100
svg_width = 3 * w + 2 * gap
svg_height = 2 * h + gap

# panel border: tab-and-slot finger joints. tab/groove depth = material thickness.
material_thickness = 3.175   # 1/8" acrylic in mm
tab_width = min(w, h) / 6   # joint width (larger = more defined edges)
locking_notch_width = tab_width / 2   # narrow center groove on two opposite edges

mt = material_thickness
tw = tab_width
lnw = locking_notch_width

# flat lengths: edge = flat+tab+flat+groove+flat+tab+flat. With locking notch: 4*flat + 2*tw + lnw = edge. With full groove: 4*flat + 3*tw = edge.
f_top = (w - 2 * tw - lnw) / 4   # top/bottom (horizontal) edges: narrow center groove
f_side = (h - 3 * tw) / 4        # left/right (vertical) edges: full-width center groove

# rectangular panel path: flat->tab->flat->groove->flat->tab->flat on each edge. Top/bottom get locking notch; left/right get full groove.
rect_path = (
    f"M 0,0 L {f_top},0 L {f_top},{-mt} L {f_top+tw},{-mt} L {f_top+tw},0 L {2*f_top+tw},0 "
    f"L {2*f_top+tw},{mt} L {2*f_top+tw+lnw},{mt} L {2*f_top+tw+lnw},0 L {3*f_top+tw},0 L {3*f_top+tw},{-mt} L {3*f_top+2*tw},{-mt} L {3*f_top+2*tw},0 L {w},0 "
    f"L {w},{f_side} L {w+mt},{f_side} L {w+mt},{f_side+tw} L {w},{f_side+tw} L {w},{2*f_side+tw} L {w-mt},{2*f_side+tw} L {w-mt},{2*f_side+2*tw} L {w},{2*f_side+2*tw} L {w},{3*f_side+2*tw} L {w+mt},{3*f_side+2*tw} L {w+mt},{3*f_side+3*tw} L {w},{3*f_side+3*tw} L {w},{h} "
    f"L {3*f_top+2*tw},{h} L {3*f_top+2*tw},{h+mt} L {3*f_top+tw},{h+mt} L {3*f_top+tw},{h} L {2*f_top+tw+lnw},{h} L {2*f_top+tw+lnw},{h-mt} L {2*f_top+tw},{h-mt} L {2*f_top+tw},{h} L {f_top+tw},{h} L {f_top+tw},{h+mt} L {f_top},{h+mt} L {f_top},{h} L 0,{h} "
    f"L 0,{3*f_side+2*tw} L {-mt},{3*f_side+2*tw} L {-mt},{3*f_side+tw} L 0,{3*f_side+tw} L 0,{2*f_side+tw} L {mt},{2*f_side+tw} L {mt},{2*f_side} L 0,{2*f_side} L 0,{f_side+tw} L {-mt},{f_side+tw} L {-mt},{f_side} L 0,{f_side} L 0,0 Z"
)

# square panel: same pattern. Top/bottom = locking notch; left/right = full groove. Edge length = w.
f_sq_top = (w - 2 * tw - lnw) / 4
f_sq_side = (w - 3 * tw) / 4
square_path = (
    f"M 0,0 L {f_sq_top},0 L {f_sq_top},{-mt} L {f_sq_top+tw},{-mt} L {f_sq_top+tw},0 L {2*f_sq_top+tw},0 "
    f"L {2*f_sq_top+tw},{mt} L {2*f_sq_top+tw+lnw},{mt} L {2*f_sq_top+tw+lnw},0 L {3*f_sq_top+tw},0 L {3*f_sq_top+tw},{-mt} L {3*f_sq_top+2*tw},{-mt} L {3*f_sq_top+2*tw},0 L {w},0 "
    f"L {w},{f_sq_side} L {w+mt},{f_sq_side} L {w+mt},{f_sq_side+tw} L {w},{f_sq_side+tw} L {w},{2*f_sq_side+tw} L {w-mt},{2*f_sq_side+tw} L {w-mt},{2*f_sq_side+2*tw} L {w},{2*f_sq_side+2*tw} L {w},{3*f_sq_side+2*tw} L {w+mt},{3*f_sq_side+2*tw} L {w+mt},{3*f_sq_side+3*tw} L {w},{3*f_sq_side+3*tw} L {w},{w} "
    f"L {3*f_sq_top+2*tw},{w} L {3*f_sq_top+2*tw},{w+mt} L {3*f_sq_top+tw},{w+mt} L {3*f_sq_top+tw},{w} L {2*f_sq_top+tw+lnw},{w} L {2*f_sq_top+tw+lnw},{w-mt} L {2*f_sq_top+tw},{w-mt} L {2*f_sq_top+tw},{w} L {f_sq_top+tw},{w} L {f_sq_top+tw},{w+mt} L {f_sq_top},{w+mt} L {f_sq_top},{w} L 0,{w} "
    f"L 0,{3*f_sq_side+2*tw} L {-mt},{3*f_sq_side+2*tw} L {-mt},{3*f_sq_side+tw} L 0,{3*f_sq_side+tw} L 0,{2*f_sq_side+tw} L {mt},{2*f_sq_side+tw} L {mt},{2*f_sq_side} L 0,{2*f_sq_side} L 0,{f_sq_side+tw} L {-mt},{f_sq_side+tw} L {-mt},{f_sq_side} L 0,{f_sq_side} L 0,0 Z"
)

# bolt holes inside panel (not on tabs). 2-56 nut clearance.
nut_hole_radius_mm = 3.35
circle_radius = nut_hole_radius_mm
# hole centers: near the middle of each edge, inset so they are inside the panel
hole_inset = 35   # mm from edge midpoint inward (top/right/bottom/left)

total_w = max(svg_width, x + svg_width)
total_h = max(svg_height, y + svg_height)
margin = mt + tw
view_w = total_w + 2 * margin
view_h = total_h + 2 * margin

#Write SVG File
file = open("gcode_file.svg", "w")
file.write('<?xml version="1.0" encoding="UTF-8" ?>')
file.write('\n')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" ')
file.write(f'viewBox="-{margin} -{margin} {view_w} {view_h}" width="{view_w}" height="{view_h}">')
file.write('\n')
outline_stroke = max(stroke_width, 1.5)   # at least 1.5 so edges are clearly visible
file.write(f'  <g transform="translate({x + margin}, {y + margin})" stroke="black" stroke-width="{outline_stroke}" fill="none">')
file.write('\n')

file.write('    <g transform="translate(0, 0)">')
file.write('\n')
file.write(f'      <path d="{rect_path}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({w + gap}, 0)">')
file.write('\n')
file.write(f'      <path d="{rect_path}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({2*w + 2*gap}, 0)">')
file.write('\n')
file.write(f'      <path d="{square_path}" />')
file.write('\n')
file.write(f'      <circle cx="{w/2}" cy="{hole_inset}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{w - hole_inset}" cy="{w/2}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{w/2}" cy="{w - hole_inset}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{hole_inset}" cy="{w/2}" r="{circle_radius}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate(0, {h + gap})">')
file.write('\n')
file.write(f'      <path d="{rect_path}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({w + gap}, {h + gap})">')
file.write('\n')
file.write(f'      <path d="{rect_path}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({2*w + 2*gap}, {h + gap})">')
file.write('\n')
file.write(f'      <path d="{square_path}" />')
file.write('\n')
file.write(f'      <circle cx="{w/2}" cy="{hole_inset}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{w - hole_inset}" cy="{w/2}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{w/2}" cy="{w - hole_inset}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{hole_inset}" cy="{w/2}" r="{circle_radius}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write('  </g>')
file.write('\n')
file.write('</svg>')
file.write('\n')
file.close()
