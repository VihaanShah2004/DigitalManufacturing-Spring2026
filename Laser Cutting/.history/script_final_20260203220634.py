#Vihaan Shah
#UNI: vvs2119
#MECE4606 Digital Manufacturing
#Laser Cutting Project

import math

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
gap = 10
jd_short = w / 3
jd_long = h / 5
# 2-56 square nut: width across corners ~0.256" (6.5 mm). Hole radius for nut clearance (mm).
nut_hole_radius_mm = 3.35  # diameter 6.7 mm, clears 6.5 mm nut with small play
circle_radius = nut_hole_radius_mm
svg_width = 3 * w + 2 * gap
svg_height = 2 * h + gap

# one rectangular panel path (width x height, finger joints)
rect_path = f"M 0,0 L {w/3},0 L {w/3},{jd_short} L {2*w/3},{jd_short} L {2*w/3},0 L {w},0 L {w},{h/5} L {w-jd_long},{h/5} L {w-jd_long},{2*h/5} L {w},{2*h/5} L {w},{3*h/5} L {w-jd_long},{3*h/5} L {w-jd_long},{4*h/5} L {w},{4*h/5} L {w},{h} L {2*w/3},{h} L {2*w/3},{h-jd_short} L {w/3},{h-jd_short} L {w/3},{h} L 0,{h} L 0,{4*h/5} L {jd_long},{4*h/5} L {jd_long},{3*h/5} L 0,{3*h/5} L 0,{2*h/5} L {jd_long},{2*h/5} L {jd_long},{h/5} L 0,{h/5} L 0,0 Z"

# one square panel path (top/bottom, finger joints)
square_path = f"M 0,0 L {w/3},0 L {w/3},{jd_short} L {2*w/3},{jd_short} L {2*w/3},0 L {w},0 L {w},{w/3} L {w-jd_short},{w/3} L {w-jd_short},{2*w/3} L {w},{2*w/3} L {w},{w} L {2*w/3},{w} L {2*w/3},{w-jd_short} L {w/3},{w-jd_short} L {w/3},{w} L 0,{w} L 0,{2*w/3} L {jd_short},{2*w/3} L {jd_short},{w/3} L 0,{w/3} L 0,0 Z"

total_w = max(svg_width, x + svg_width)
total_h = max(svg_height, y + svg_height)

# recursive branching: returns list of (x1, y1, x2, y2). angle in degrees, curvature added per level.
def branch_segments(px, py, length, angle_deg, depth, branch_angle, length_scale, curvature=0):
    rad = math.radians(angle_deg)
    x2 = px + length * math.cos(rad)
    y2 = py + length * math.sin(rad)
    segs = [(px, py, x2, y2)]
    if depth <= 0:
        return segs
    new_angle = angle_deg + curvature
    new_length = length * length_scale
    segs.extend(branch_segments(x2, y2, new_length, new_angle + branch_angle, depth - 1, branch_angle, length_scale, curvature))
    segs.extend(branch_segments(x2, y2, new_length, new_angle - branch_angle, depth - 1, branch_angle, length_scale, curvature))
    return segs

# Pattern A: symmetric tree. Pattern B: curved tree (curvature_per_level).
init_len = h * 0.12
pattern_a_segs = branch_segments(w/2, h, init_len, -90, 8, 25, 0.7, 0)
pattern_b_segs = branch_segments(w/2, h, init_len, -90, 8, 22, 0.7, 4)

#Write SVG File
file = open("gcode_file.svg", "w")
file.write('<?xml version="1.0" encoding="UTF-8" ?>')
file.write('\n')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" ')
file.write(f'viewBox="0 0 {total_w} {total_h}" width="{total_w}" height="{total_h}">')
file.write('\n')
file.write(f'  <g transform="translate({x}, {y})" stroke="black" stroke-width="{stroke_width}" fill="none">')
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
file.write(f'      <circle cx="{w/2}" cy="{jd_short/2}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{w - jd_short/2}" cy="{w/2}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{w/2}" cy="{w - jd_short/2}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{jd_short/2}" cy="{w/2}" r="{circle_radius}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate(0, {h + gap})">')
file.write('\n')
file.write(f'      <path d="{rect_path}" />')
file.write('\n')
for x1, y1, x2, y2 in pattern_a_segs:
    file.write(f'      <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="red" stroke-width="{stroke_width}" />')
    file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({w + gap}, {h + gap})">')
file.write('\n')
file.write(f'      <path d="{rect_path}" />')
file.write('\n')
for x1, y1, x2, y2 in pattern_b_segs:
    file.write(f'      <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="red" stroke-width="{stroke_width}" />')
    file.write('\n')
file.write('    </g>')
file.write('\n')

file.write(f'    <g transform="translate({2*w + 2*gap}, {h + gap})">')
file.write('\n')
file.write(f'      <path d="{square_path}" />')
file.write('\n')
file.write(f'      <circle cx="{w/2}" cy="{jd_short/2}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{w - jd_short/2}" cy="{w/2}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{w/2}" cy="{w - jd_short/2}" r="{circle_radius}" />')
file.write('\n')
file.write(f'      <circle cx="{jd_short/2}" cy="{w/2}" r="{circle_radius}" />')
file.write('\n')
file.write('    </g>')
file.write('\n')

file.write('  </g>')
file.write('\n')
file.write('</svg>')
file.write('\n')
file.close()
