file = open("demofile.svg", "w")
file.write("Hello %i World %5.2f\n" % (5, 2.2))
file.close()