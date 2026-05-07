import math

# ==========================================
# MACHINE CALIBRATION
# ==========================================
X_OFFSET_T1 = -24.375
Y_OFFSET_T1 = 0.95
Z_OFFSET_T1 = 0.25
SYRINGE_ID  = 10.0
SAFE_X, SAFE_Y = 30, 30
NUM_LAYERS  = 1

# ==========================================
# MATERIAL PROFILE
# ==========================================
class MaterialProfile:
    def _init_(self, name, nozzle_dia, ext_multiplier, feed_rate, prime_amount):
        self.name           = name
        self.nozzle_dia     = nozzle_dia
        self.ext_multiplier = ext_multiplier
        self.feed_rate      = feed_rate
        self.prime_amount   = prime_amount

PROFILES = {
    'T0': MaterialProfile("Cream Cheese",  1.2, 30, 300, 0.375),
    'T1': MaterialProfile("Peanut Butter", 1.2, 30, 300, 0.375)
}

# ==========================================
# G-CODE ENGINE  (unchanged from reference)
# ==========================================
class FoodGCodeGenerator:
    def _init_(self, filename="spiro_output.nc"):
        self.filename     = filename
        self.current_tool = "T0"
        self.total_e      = {"T0": 0.0, "T1": 0.0}
        self.gcode        = []

    def calculate_extrusion(self, distance, tool_id):
        profile = PROFILES[tool_id]
        ratio   = (SYRINGE_ID / profile.nozzle_dia)**2 * profile.ext_multiplier
        return distance / ratio

    def process_coordinates(self, coord_list):
        self.gcode.append("M106 S255 ; Fan On")
        self.gcode.append("G21 ; mm")
        self.gcode.append("G90 ; Absolute")

        # Prime both tools
        for tool in ['T0', 'T1']:
            p = PROFILES[tool]
            self.gcode.append(f"\n; Priming {tool}")
            self.gcode.append(tool)
            self.total_e[tool] += p.prime_amount
            self.gcode.append(f"G1 X{SAFE_X} Y{SAFE_Y} Z30 F1000")
            self.gcode.append(f"G1 E{self.total_e[tool]:.5f} F{p.feed_rate/2}")
            self.gcode.append("G4 P2000")

        self.gcode.append("G92 E0")
        self.gcode.append("T0")

        last_x, last_y = 60, 60
        last_z = 0.6
        first_point = True

        for item in coord_list:
            if len(item) == 1:
                continue

            x, y, z, mode, layer_idx = item
            profile = PROFILES[self.current_tool]

            if mode == "T" and first_point:
                # Only lift and travel for the very first point
                self.gcode.append(f"G0 Z{z + 5:.3f} F1000 ; Lift to start")
                self.gcode.append(f"G0 X{x:.3f} Y{y:.3f} F1000")
                self.gcode.append(f"G0 Z{z:.3f} F300 ; Lower to print height")
                first_point = False
            else:
                # Everything else is a continuous extrude — never lift mid-shape
                dist = math.sqrt((x - last_x)*2 + (y - last_y)*2)
                self.total_e[self.current_tool] += self.calculate_extrusion(dist, self.current_tool)
                self.gcode.append(
                    f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f} "
                    f"E{self.total_e[self.current_tool]:.5f} F{profile.feed_rate}"
                )

            last_x, last_y, last_z = x, y, z

        self.gcode.append("\n; Shutdown")
        self.gcode.append(f"G0 Z{last_z + 20:.3f} F500")
        self.gcode.append("M106 S0")
        self.gcode.append("M84")
        return "\n".join(self.gcode)


# ==========================================
# SPIROGRAPH GEOMETRY
# ==========================================
def generate_spirograph(R, r, d, revolutions, points_per_rev, z_height, offset_x, offset_y):
    """
    Traces the FULL spirograph shape as one single continuous stroke.
    Only the very first point is a travel (T). All others are extrude (E).
    The nozzle never lifts mid-shape.

    total_points = revolutions * points_per_rev
    t goes from 0 to 2*pi*revolutions continuously
    """
    coords       = []
    total_points = revolutions * points_per_rev

    for i in range(total_points + 1):
        # t increases continuously from 0 to 2*pi*revolutions
        t = (2 * math.pi * revolutions * i) / total_points
        x = (R - r) * math.cos(t) + d * math.cos(((R - r) / r) * t) + offset_x
        y = (R - r) * math.sin(t) - d * math.sin(((R - r) / r) * t) + offset_y
        mode = "T" if i == 0 else "E"
        coords.append([x, y, z_height, mode, 0])

    return coords


def generate_concentric_fill(R, r, d, z_height, offset_x, offset_y):
    """
    Fills the inside of the spirograph with concentric circles,
    shrinking inward until the center is filled.

    max_radius is estimated from the spirograph parameters as
    the approximate inner boundary of the outermost curve.
    """
    profile     = PROFILES['T0']
    max_radius  = abs((R - r) - d)
    step_size   = profile.nozzle_dia * 0.9
    fill_coords = []

    current_radius = max_radius
    while current_radius > 0.5:
        # More points for larger circles so the curve stays smooth
        num_points = max(8, int(2 * math.pi * current_radius))

        for i in range(num_points + 1):
            t    = (2 * math.pi * i) / num_points
            x    = current_radius * math.cos(t) + offset_x
            y    = current_radius * math.sin(t) + offset_y
            mode = "T" if i == 0 else "E"
            fill_coords.append([x, y, z_height, mode, 0])

        current_radius -= step_size

    return fill_coords


# ==========================================
# SETTINGS — tweak these to change the shape
# ==========================================

R_VAL  = 36    # fixed circle radius (mm)
R_SMALL = 8    # rolling circle radius (mm)
D_VAL  = 20    # pen distance (mm)

# How many times the inner circle goes around
# more revolutions = more petals traced = denser pattern
REVOLUTIONS    = 9     # needed to complete the full closed flower shape
POINTS_PER_REV = 200   # smoothness per revolution

Z_VAL  = 0.6   # print height (mm above bed)
OFF_X  = 60    # center of pattern X on bed (mm)
OFF_Y  = 60    # center of pattern Y on bed (mm)

ADD_FILL = True  # concentric circles fill the center void


# ==========================================
# RUN
# ==========================================
if _name_ == "_main_":

    print("Generating spirograph coordinates...")
    print(f"  R={R_VAL}mm  r={R_SMALL}mm  d={D_VAL}mm")
    print(f"  Revolutions: {REVOLUTIONS}  Points/rev: {POINTS_PER_REV}")
    print(f"  Z height: {Z_VAL}mm")
    print(f"  Center: ({OFF_X}, {OFF_Y})")
    print(f"  Fill: {'yes' if ADD_FILL else 'no'}")
    print()

    # 1. Outer spirograph curve
    coords = generate_spirograph(
        R=R_VAL, r=R_SMALL, d=D_VAL,
        revolutions=REVOLUTIONS,
        points_per_rev=POINTS_PER_REV,
        z_height=Z_VAL,
        offset_x=OFF_X,
        offset_y=OFF_Y
    )
    print(f"  Spirograph points: {len(coords)}")

    # 2. Concentric fill inside
    if ADD_FILL:
        fill = generate_concentric_fill(
            R=R_VAL, r=R_SMALL, d=D_VAL,
            z_height=Z_VAL,
            offset_x=OFF_X,
            offset_y=OFF_Y
        )
        coords.extend(fill)
        print(f"  Fill points added: {len(fill)}")

    print(f"  Total coords: {len(coords)}")

    # 3. Generate G-code
    output_filename = "spirograph.nc"
    engine = FoodGCodeGenerator(output_filename)
    gcode  = engine.process_coordinates(coords)

    with open(output_filename, "w") as f:
        f.write(gcode)

    print(f"\nSaved: {output_filename}")
    print("Test at: https://nraynaud.github.io/webgcode/")

    try:
        from google.colab import files
        files.download(output_filename)
        print("Downloading...")
    except ImportError:
        print(f"File saved locally: {output_filename}")