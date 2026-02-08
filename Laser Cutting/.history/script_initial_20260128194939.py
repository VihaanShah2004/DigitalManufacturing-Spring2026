#Vihaan Shah
#MECE4606 Digital Manufacturing
#Laser Cutting Project

#Gather Input
x = input("Type x coordinate to start")
y = input("Type y coordinate to start")
width = input("Type width coordinate to start")
height = input("Type height coordinate to start")
stroke_width = input("Type stroke width coordinate to start")
 = input("Type y coordinate to start")

#Write SVG File
file = open("demofile.svg", "w")
file.write('<?xml version="1.0" encoding="UTF-8" ?>')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">')
file.write('<rect x="0" y="0" width="30" height="20" rx="3" ry="3" style="stroke-width:1;stroke:rgb(0,0,0);fill:none" />')
file.close()