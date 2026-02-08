#Vihaan Shah
#UNI: vvs2119
#MECE4606 Digital Manufacturing
#Laser Cutting Project

#Gather Input
try:
    x = float(input("Type x coordinate to start (mm): "))
    y = float(input("Type y coordinate to start (mm): "))
    z = float(input("Type z coordinate to start (mm): "))
    length = float(input("Type length to start (mm): "))
    width = float(input("Type width to start (mm): "))
    height = float(input("Type height to start (mm): "))
    stroke_width = float(input("Type stroke width to start (mm): "))
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
circle_radius = w / 15
svg_width = 3 * w + 2 * gap
svg_height = 2 * h + gap

# one rectangular panel path (width x height, finger joints)
rect_path = f"M 0,0 L {w/3},0 L {w/3},{jd_short} L {2*w/3},{jd_short} L {2*w/3},0 L {w},0 L {w},{h/5} L {w-jd_long},{h/5} L {w-jd_long},{2*h/5} L {w},{2*h/5} L {w},{3*h/5} L {w-jd_long},{3*h/5} L {w-jd_long},{4*h/5} L {w},{4*h/5} L {w},{h} L {2*w/3},{h} L {2*w/3},{h-jd_short} L {w/3},{h-jd_short} L {w/3},{h} L 0,{h} L 0,{4*h/5} L {jd_long},{4*h/5} L {jd_long},{3*h/5} L 0,{3*h/5} L 0,{2*h/5} L {jd_long},{2*h/5} L {jd_long},{h/5} L 0,{h/5} L 0,0 Z"

# one square panel path (top/bottom, finger joints)
square_path = f"M 0,0 L {w/3},0 L {w/3},{jd_short} L {2*w/3},{jd_short} L {2*w/3},0 L {w},0 L {w},{w/3} L {w-jd_short},{w/3} L {w-jd_short},{2*w/3} L {w},{2*w/3} L {w},{w} L {2*w/3},{w} L {2*w/3},{w-jd_short} L {w/3},{w-jd_short} L {w/3},{w} L 0,{w} L 0,{2*w/3} L {jd_short},{2*w/3} L {jd_short},{w/3} L 0,{w/3} L 0,0 Z"

total_w = max(svg_width, x + svg_width)
total_h = max(svg_height, y + svg_height)

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
