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

# panel border: corners = inward slots; edges = tab-slot pattern per image.
material_thickness = 3.175   # 1/8" acrylic in mm
tab_width = min(w, h) / 8   # keep flat segments positive (need 6*tw < w for rect top)
mt = material_thickness
tw = tab_width
cs = tw   # corner slot width (along each edge)
t_w = tw / 2   # T-shaped locking notch: small protrusion width

# RECT PANEL (tall): horizontal edges = 2 tabs + shallow slot with T-notch. Vertical edges = 3 tabs, 2 slots.
flat_rect_top = (w - 2 * cs - 2 * tw - 2 * tw) / 2
flat_rect_side = (h - 2 * mt - 5 * tw) / 4
# T-notch: center groove 2*tw wide, small protrusion (t_w) in middle
rect_pts = [
    (tw, 0), (tw, -mt), (2*tw, -mt), (2*tw, 0), (2*tw+flat_rect_top, 0),
    (2*tw+flat_rect_top, mt), (2*tw+flat_rect_top+tw-t_w/2, mt), (2*tw+flat_rect_top+tw-t_w/2, 0), (2*tw+flat_rect_top+tw+t_w/2, 0), (2*tw+flat_rect_top+tw+t_w/2, mt), (4*tw+flat_rect_top, mt), (4*tw+flat_rect_top, 0),
    (4*tw+2*flat_rect_top, 0), (4*tw+2*flat_rect_top, -mt), (w-tw, -mt), (w-tw, 0),
    (w, 0), (w, mt),
    (w+mt, mt), (w+mt, mt+tw), (w, mt+tw), (w, mt+tw+flat_rect_side), (w-mt, mt+tw+flat_rect_side), (w-mt, mt+tw+flat_rect_side+tw), (w, mt+tw+flat_rect_side+tw), (w, mt+2*tw+2*flat_rect_side), (w+mt, mt+2*tw+2*flat_rect_side), (w+mt, mt+3*tw+2*flat_rect_side), (w, mt+3*tw+2*flat_rect_side), (w, mt+3*tw+3*flat_rect_side), (w-mt, mt+3*tw+3*flat_rect_side), (w-mt, mt+4*tw+3*flat_rect_side), (w, mt+4*tw+3*flat_rect_side), (w+mt, mt+4*tw+3*flat_rect_side), (w+mt, h-mt), (w, h-mt),
    (w, h), (w-tw, h),
    (4*tw+2*flat_rect_top, h), (4*tw+2*flat_rect_top, h+mt), (4*tw+flat_rect_top, h+mt), (4*tw+flat_rect_top, h), (2*tw+flat_rect_top+tw+t_w/2, h), (2*tw+flat_rect_top+tw+t_w/2, h-mt), (2*tw+flat_rect_top+tw-t_w/2, h-mt), (2*tw+flat_rect_top+tw-t_w/2, h), (2*tw+flat_rect_top, h), (2*tw+flat_rect_top, h-mt), (2*tw, h-mt), (2*tw, h), (tw, h), (tw, h+mt), (tw, h), (0, h),
    (0, h), (0, h-mt),
    (-mt, h-mt), (-mt, h-mt-tw), (0, h-mt-tw), (0, h-mt-tw-flat_rect_side), (mt, h-mt-tw-flat_rect_side), (mt, h-mt-2*tw-flat_rect_side), (0, h-mt-2*tw-flat_rect_side), (0, h-mt-2*tw-2*flat_rect_side), (-mt, h-mt-2*tw-2*flat_rect_side), (-mt, h-mt-3*tw-2*flat_rect_side), (0, h-mt-3*tw-2*flat_rect_side), (0, h-mt-3*tw-3*flat_rect_side), (mt, h-mt-3*tw-3*flat_rect_side), (mt, h-mt-4*tw-3*flat_rect_side), (-mt, h-mt-4*tw-3*flat_rect_side), (-mt, mt), (0, mt),
    (0, 0), (tw, 0),
]

# SQUARE PANEL: horizontal = 3 tabs, 2 slots. Vertical = 2 tabs, 1 slot. No T-notch.
flat_sq_h = (w - 2 * cs - 5 * tw) / 4
flat_sq_v = (w - 2 * mt - 3 * tw) / 2
square_pts = [
    (tw, 0), (tw, -mt), (2*tw, -mt), (2*tw, 0), (2*tw+flat_sq_h, 0), (2*tw+flat_sq_h, mt), (3*tw+flat_sq_h, mt), (3*tw+flat_sq_h, 0), (3*tw+2*flat_sq_h, 0), (3*tw+2*flat_sq_h, -mt), (4*tw+2*flat_sq_h, -mt), (4*tw+2*flat_sq_h, 0), (4*tw+3*flat_sq_h, 0), (4*tw+3*flat_sq_h, mt), (5*tw+3*flat_sq_h, mt), (5*tw+3*flat_sq_h, 0), (w-tw, 0),
    (w, 0), (w, mt),
    (w+mt, mt), (w+mt, mt+tw), (w, mt+tw), (w, mt+tw+flat_sq_v), (w-mt, mt+tw+flat_sq_v), (w-mt, mt+2*tw+flat_sq_v), (w, mt+2*tw+flat_sq_v), (w, w-mt),
    (w, w), (w-tw, w),
    (w-tw, w+mt), (w-2*tw, w+mt), (w-2*tw, w), (w-2*tw-flat_sq_h, w), (w-2*tw-flat_sq_h, w-mt), (w-3*tw-flat_sq_h, w-mt), (w-3*tw-flat_sq_h, w), (w-3*tw-2*flat_sq_h, w), (w-3*tw-2*flat_sq_h, w+mt), (w-4*tw-2*flat_sq_h, w+mt), (w-4*tw-2*flat_sq_h, w), (w-4*tw-3*flat_sq_h, w), (w-4*tw-3*flat_sq_h, w-mt), (w-5*tw-3*flat_sq_h, w-mt), (w-5*tw-3*flat_sq_h, w), (tw, w),
    (tw, w+mt), (tw, w), (0, w),
    (0, w), (0, w-mt),
    (-mt, w-mt), (-mt, w-mt-tw), (0, w-mt-tw), (0, w-mt-tw-flat_sq_v), (mt, w-mt-tw-flat_sq_v), (mt, w-mt-2*tw-flat_sq_v), (0, w-mt-2*tw-flat_sq_v), (0, w-mt-2*tw-2*flat_sq_v), (-mt, w-mt-2*tw-2*flat_sq_v), (-mt, mt), (0, mt),
    (0, 0), (tw, 0),
]

def points_to_polyline(points):
    return " ".join(f"{px},{py}" for px, py in points)

# bolt holes inside panel: aligned with nut grooves (nuts sit at edge, groove = material thickness). Hole at edge center, inset by mt so in line with nut.
nut_hole_radius_mm = 3.35
circle_radius = nut_hole_radius_mm
# hole centers = edge midpoint, one material thickness inward (in line with nut groove)
hole_inset = mt

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
# stroke width: cap so tabs stay visible (stroke is centered on line; too thick obscures narrow features)
outline_stroke = min(stroke_width, mt / 2, tw / 4)
if outline_stroke <= 0:
    outline_stroke = 0.5
file.write(f'  <g transform="translate({x + margin}, {y + margin})" stroke="black" stroke-width="{outline_stroke}" fill="none" stroke-linejoin="miter" stroke-linecap="butt">')
file.write('\n')

rect_points_str = points_to_polyline(rect_pts)
square_points_str = points_to_polyline(square_pts)

file.write('    <g transform="translate(0, 0)">')
file.write('\n')
file.write(f'      <polygon points="{rect_points_str}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({w + gap}, 0)">')
file.write('\n')
file.write(f'      <polygon points="{rect_points_str}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({2*w + 2*gap}, 0)">')
file.write('\n')
file.write(f'      <polygon points="{square_points_str}" />')
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
file.write(f'      <polygon points="{rect_points_str}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({w + gap}, {h + gap})">')
file.write('\n')
file.write(f'      <polygon points="{rect_points_str}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({2*w + 2*gap}, {h + gap})">')
file.write('\n')
file.write(f'      <polygon points="{square_points_str}" />')
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
