; pyramid.gcode — 5-layer equilateral-triangle pyramid, centered at (100, 100)
; All layers share the same centroid (100,100) — perfectly stacked.
; Each layer is an equilateral triangle shrinking 6 mm per side, rising 2 mm in Z.
;
; Layer 1: s=30 mm  Z=8.3   V1(100,117.3)  V2(85,91.3)   V3(115,91.3)
; Layer 2: s=24 mm  Z=9.3   V1(100,113.9)  V2(88,93.1)   V3(112,93.1)
; Layer 3: s=18 mm  Z=11.3  V1(100,110.4)  V2(91,94.8)   V3(109,94.8)
; Layer 4: s=12 mm  Z=13.3  V1(100,106.9)  V2(94,96.5)   V3(106,96.5)
; Layer 5: s=6  mm  Z=15.3  V1(100,103.5)  V2(97,98.3)   V3(103,98.3)
;
; Centroid (100,100) is the center of every layer — layers stack directly above each other.
; E values cumulative absolute, reduced to ~0.10/mm to avoid over-extrusion.

G21       ; millimeters
G90       ; absolute positioning
G92 E0    ; reset extruder
M82       ; absolute extrusion mode
M106 S255 ; start fans at full speed to prevent motor overheat

; --- Optional: uncomment to home before print ---
; G28 X Y Z

; ── LAYER 1 — s=30 mm, Z=8.3 ────────────────────────────────────────
; Prime: approach 5 mm below top vertex to get paste flowing before corner.
G0 Z13 F600
G0 X100.0 Y112.3 F3000
G0 Z8.3 F600
G4 P150
G1 X100.0 Y117.3 E1.0 F300

G1 X115.0 Y91.3 E4.6 F400
G4 P80
G1 X85.0 Y91.3 E7.6 F400
G4 P80
G1 X100.0 Y117.3 E10.6 F400

; ── LAYER 2 — s=24 mm, Z=9.3 ────────────────────────────────────────
G0 Z9.8 F600
G0 X100.0 Y113.9 F3000
G0 Z9.3 F600
G4 P120

G1 X112.0 Y93.1 E13.5 F400
G4 P80
G1 X88.0 Y93.1 E15.9 F400
G4 P80
G1 X100.0 Y113.9 E18.3 F400

; ── LAYER 3 — s=18 mm, Z=11.3 ───────────────────────────────────────
G0 Z10.8 F600
G0 X100.0 Y110.4 F3000
G0 Z11.3 F600
G4 P120

G1 X109.0 Y94.8 E20.4 F400
G4 P80
G1 X91.0 Y94.8 E22.2 F400
G4 P80
G1 X100.0 Y110.4 E24.0 F400

; ── LAYER 4 — s=12 mm, Z=13.3 ───────────────────────────────────────
G0 Z12.8 F600
G0 X100.0 Y106.9 F3000
G0 Z13.3 F600
G4 P120

G1 X106.0 Y96.5 E25.5 F400
G4 P80
G1 X94.0 Y96.5 E26.7 F400
G4 P80
G1 X100.0 Y106.9 E27.9 F400

; ── LAYER 5 — s=6 mm, Z=15.3 ────────────────────────────────────────
G0 Z14.8 F600
G0 X100.0 Y103.5 F3000
G0 Z15.3 F600
G4 P120

G1 X103.0 Y98.3 E28.6 F400
G4 P80
G1 X97.0 Y98.3 E29.2 F400
G4 P80
G1 X100.0 Y103.5 E29.8 F400

; ── Lift and park ─────────────────────────────────────────────────────
G0 Z20 F600
G0 X0 Y0 F3000

M84       ; disable motor hold
M106 S0   ; disable fans
M2        ; program end (use M30 if your controller expects it)
