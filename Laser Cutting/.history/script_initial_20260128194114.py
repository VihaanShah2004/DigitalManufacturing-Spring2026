f = open("demofile.svg", "w")
f.write(“Hello %i World %5.2f\n" % (5, 2.2))
f.close()