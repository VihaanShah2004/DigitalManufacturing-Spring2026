; square.gcode — 50 mm square in XY at fixed Z
; Units: millimeters, absolute positioning. Adjust F (feed), Z, and XY origin as needed.

G21       ; millimeters
G90       ; absolute positioning
G92 E0    ; reset extruder counter (harmless if unused; remove if your firmware errors)

; --- Optional: uncomment to home before the path ---
; G28 X Y Z

; Safe travel height, then move to first corner (adjust Z for your first layer / nozzle height)
G0 Z5 F600
G0 X50 Y50 F3000
G0 Z0.3 F600

; Trace square: 50 mm per side (corners at 50,50 → 100,50 → 100,100 → 50,100 → 50,50)
G1 X100 Y50 F1200
G1 X100 Y100 F1200
G1 X50 Y100 F1200
G1 X50 Y50 F1200

; Lift and park (optional)
G0 Z5 F600
G0 X0 Y0 F3000

M2        ; program end (use M30 if your controller expects it)
