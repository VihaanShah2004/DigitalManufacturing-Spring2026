

#Write SVG File
file = open("demofile.svg", "w")
file.write('<?xml version="1.0" encoding="UTF-8" ?>')
file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">')
file.write('<rect x="0" y="0" width="30" height="20" rx="3" ry="3" style="stroke-width:1;stroke:rgb(0,0,0);fill:none" />')
file.close()