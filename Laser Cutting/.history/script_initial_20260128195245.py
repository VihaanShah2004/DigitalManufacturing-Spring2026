#Vihaan Shah
#MECE4606 Digital Manufacturing
#Laser Cutting Project

#Gather Input
x = input("Type x coordinate to start")
y = input("Type y coordinate to start")
width = input("Type width to start")
height = input("Type height to start")
stroke_width = input("Type stroke width to start")
fill_color = input("Type fill color to start")
stroke_color = input("Type stroke color to start")

#Write SVG File
file = open("demofile.svg", "w")
file.write('<?xml version="1.0" encoding="UTF-8" ?>')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">')
file.write(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" ry="3" style="stroke-width:{stroke_width};stroke:{stroke_color};fill:{fill_color}" />')
file.close()