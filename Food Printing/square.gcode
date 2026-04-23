; square.gcode — 50 mm square in XY at fixed Z
; Units: millimeters, absolute positioning.
; Updated: lower print Z and add extrusion on each segment.

G21       ; millimeters
G90       ; absolute positioning
G92 E0    ; reset extruder counter (harmless if unused; remove if your firmware errors)
M82       ; absolute extrusion mode (common on Marlin/Reprap)
M106 S255 ; start fans at full speed to prevent motor overheat

; --- Optional: uncomment to home before the path ---
; G28 X Y Z

; Safe travel height, then approach a prime point 5 mm before the first corner.
G0 Z5 F600
G0 X25 Y30 F3000
G0 Z5 F600
G4 P150    ; settle time before extrusion starts

; Prime: extrude 5 mm along Y=30 into the first corner to get paste flowing.
; This ensures no missing material at the start of the actual square edge.
G1 X30 Y30 E2.0 F300

; Trace square: 50 mm per side (corners at 30,30 → 80,30 → 80,80 → 30,80 → 30,30)
; E values are cumulative in absolute mode; tune total extrusion as needed.
; Slightly slower speed + brief corner dwells help corners print sharper.
G1 X80 Y30 E14.0 F500
G4 P80
G1 X80 Y80 E26.0 F500
G4 P80
G1 X30 Y80 E38.0 F500
G4 P80
G1 X30 Y30 E46.0 F500

; Lift and park
G0 Z5 F600
G0 X0 Y0 F3000

M84       ; disable motor hold
M106 S0   ; disable fans
M2        ; program end (use M30 if your controller expects it)
