#Vihaan Shah
#UNI: vvs2119
#MECE4606 Digital Manufacturing
#Laser Cutting Project

#Gather Input
x = input("Type x coordinate to start: ")
y = input("Type y coordinate to start: ")
z = input("Type z coordinate to start: ")
length = input("Type length to start: ")
width = input("Type width to start: ")
height = input("Type height to start: ")
stroke_width = input("Type stroke width to start: ")

#Write SVG File
file = open("gcode.svg", "w")
file.write('<?xml version="1.0" encoding="UTF-8" ?>')
file.write('\n')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">')
file.write('\n')
file.write(f'    <rect x="{x}" y="{y}" width="{width}" height="{height}" style="stroke-width:{stroke_width}" />')
file.write('\n')
file.write('</svg>')
file.write('\n')
file.close()