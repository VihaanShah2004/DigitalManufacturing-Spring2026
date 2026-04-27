import math
from pathlib import Path
from types import SimpleNamespace

FIXED_T1_OFFSET_X = 24.0
FIXED_T1_OFFSET_Y = 0.0
FIXED_T1_OFFSET_Z = 0.0
FIXED_BASE_Z = 1.0
FIXED_LAYER_HEIGHT = 1.0
FIXED_START_EXTRUSION = 3.0
FIXED_EXTRUSION_INCREMENT = 1.8


def fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def prompt_str(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value if value else default


def prompt_int(prompt: str, default: int) -> int:
    return int(prompt_str(prompt, str(default)))


def prompt_float(prompt: str, default: float) -> float:
    return float(prompt_str(prompt, str(default)))


def prompt_bool(prompt: str, default: bool) -> bool:
    default_text = "y" if default else "n"
    value = prompt_str(prompt + " (y/n)", default_text).lower()
    return value in {"y", "yes", "1", "true"}


def collect_inputs() -> SimpleNamespace:
    print("Dual-extruder shape generator")
    print("Press Enter to use defaults.")

    alternate_by = prompt_str("Tool alternation mode (layer/ring)", "layer").lower()
    if alternate_by not in {"layer", "ring"}:
        alternate_by = "layer"
    shape = prompt_str("Shape (circle/star_cookie/heart/leaf)", "star_cookie").lower()
    if shape not in {"circle", "star_cookie", "heart", "leaf"}:
        shape = "star_cookie"

    return SimpleNamespace(
        output=Path(prompt_str("Output file name", "dual_shape.gcode")),
        shape=shape,
        center_x=prompt_float("Shape center X (T0 frame)", 60.0),
        center_y=prompt_float("Shape center Y (T0 frame)", 60.0),
        base_z=FIXED_BASE_Z,
        radius=prompt_float("Shape radius (mm)", 12.0),
        layers=prompt_int("Number of layers", 14),
        layer_height=FIXED_LAYER_HEIGHT,
        segments=prompt_int("Segments per loop", 72),
        edge_e=FIXED_EXTRUSION_INCREMENT,
        travel_feed=prompt_int("Travel feedrate (mm/min)", 1600),
        print_feed=prompt_int("Print feedrate (mm/min)", 850),
        z_feed=prompt_int("Z feedrate (mm/min)", 600),
        fan=prompt_int("Fan speed (0-255)", 255),
        prime_len=prompt_float("Prime line length", 16.0),
        prime_e=prompt_float("Prime line extrusion", 1.2),
        alternate_by=alternate_by,
        rings_per_layer=prompt_int("Rings per layer", 1),
        ring_spacing=prompt_float("Ring spacing (mm)", 1.0),
        t1_offset_x=FIXED_T1_OFFSET_X,
        t1_offset_y=FIXED_T1_OFFSET_Y,
        t1_offset_z=FIXED_T1_OFFSET_Z,
        manual_offset_compensation=prompt_bool("Use manual software offset compensation", True),
    )


def circle_points(cx: float, cy: float, radius: float, segments: int) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(segments):
        angle = 2.0 * math.pi * (i / segments)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        pts.append((x, y))
    pts.append(pts[0])
    return pts


def shape_points(shape: str, cx: float, cy: float, radius: float, segments: int) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(segments):
        angle = 2.0 * math.pi * (i / segments)

        if shape == "heart":
            # Parametric heart, normalized so "radius" is the overall size driver.
            xh = 16.0 * (math.sin(angle) ** 3)
            yh = 13.0 * math.cos(angle) - 5.0 * math.cos(2.0 * angle) - 2.0 * math.cos(3.0 * angle) - math.cos(4.0 * angle)
            scale = radius / 17.0
            x = cx + xh * scale
            y = cy + yh * scale
        elif shape == "star_cookie":
            # Smooth star profile inspired by cookie-cutter geometry.
            r_local = radius * (0.55 + 0.45 * math.cos(5.0 * angle))
            x = cx + r_local * math.cos(angle)
            y = cy + r_local * math.sin(angle)
        elif shape == "leaf":
            # Almond/leaf-like silhouette with a tapered tip.
            x = cx + radius * math.cos(angle)
            y = cy + (0.55 * radius * math.sin(angle) * (1.0 + 0.35 * math.cos(angle)))
        else:
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

        pts.append((x, y))
    pts.append(pts[0])
    return pts


def tool_compensated_xy(x: float, y: float, tool: str, t1_offset_x: float, t1_offset_y: float) -> tuple[float, float]:
    if tool == "T1":
        # Compensate coordinates so T1 follows the same world path as T0.
        return x - t1_offset_x, y - t1_offset_y
    return x, y


def tool_compensated_z(z: float, tool: str, t1_offset_z: float) -> float:
    if tool == "T1":
        return z - t1_offset_z
    return z


def add_prime_sequence(
    lines: list[str],
    tool: str,
    x: float,
    y: float,
    z: float,
    prime_len: float,
    prime_e: float,
    z_feed: int,
    travel_feed: int,
    print_feed: int,
) -> None:
    lines.append(f"{tool} ; Select tool for prime")
    lines.append("G92 E0")
    lines.append(f"G0 Z{fmt(z)} F{z_feed}")
    lines.append(f"G0 X{fmt(x)} Y{fmt(y)} F{travel_feed}")
    lines.append(f"G1 X{fmt(x + prime_len)} Y{fmt(y)} E{fmt(prime_e)} F{print_feed}")
    lines.append("G92 E0")


def build_gcode(args: SimpleNamespace) -> list[str]:
    if args.layers < 1:
        raise ValueError("layers must be >= 1")
    if args.segments < 12:
        raise ValueError("segments must be >= 12")
    if args.rings_per_layer < 1:
        raise ValueError("rings-per-layer must be >= 1")
    if args.radius <= 0:
        raise ValueError("radius must be > 0")

    lines: list[str] = [
        "; Dual-extruder shape G-code (Duet)",
        "; Toolpath generated in T0 world coordinates.",
        f"; Selected shape: {args.shape}",
        "; Duet tool setup (as requested):",
        "M563 P0 D0 H1 ; Define Tool 0",
        "G10 P0 X0 Y0 Z0 ; Set Tool 0 offsets to zero",
        "M563 P1 D1 H2 ; Define Tool 1",
        f"G10 P1 X{fmt(args.t1_offset_x)} Y{fmt(args.t1_offset_y)} Z{fmt(args.t1_offset_z)} ; Set Tool 1 measured offset",
        f"; T1 offsets: X={args.t1_offset_x} Y={args.t1_offset_y} Z={args.t1_offset_z}",
        f"; Manual software compensation: {'ON' if args.manual_offset_compensation else 'OFF (firmware G10 handles offsets)'}",
        "G21 ; mm units",
        "G90 ; absolute XY",
        "M82 ; absolute extrusion",
        "G92 E0",
        f"M106 S{args.fan}",
    ]

    prime_x = args.center_x - args.radius - 10.0
    prime_y = args.center_y - args.radius - 10.0
    prime_z = max(1.0, args.base_z)

    # Prime both tools once before printing.
    add_prime_sequence(
        lines,
        "T0",
        prime_x,
        prime_y,
        prime_z,
        args.prime_len,
        args.prime_e,
        args.z_feed,
        args.travel_feed,
        args.print_feed,
    )
    add_prime_sequence(
        lines,
        "T1",
        prime_x + 4.0,
        prime_y + 4.0,
        prime_z,
        args.prime_len,
        args.prime_e,
        args.z_feed,
        args.travel_feed,
        args.print_feed,
    )

    active_tool = ""
    pending_tool_switch = False
    tool_switch_prime_e = 0.175
    tool_switch_prime_feed = max(100, args.print_feed // 2)

    for layer in range(args.layers):
        z = args.base_z + layer * args.layer_height
        lines.append(f"; --- Layer {layer + 1}/{args.layers} at Z={fmt(z)} ---")

        for ring in range(args.rings_per_layer):
            ring_radius = args.radius - ring * args.ring_spacing
            if ring_radius <= 0:
                continue

            if args.alternate_by == "ring":
                use_t0 = ((layer + ring) % 2) == 0
            else:
                use_t0 = (layer % 2) == 0
            tool = "T0" if use_t0 else "T1"

            if tool != active_tool:
                # Match the validated machine pattern: retract, switch, then re-prime.
                if active_tool:
                    safe_z = z + 3.0
                    lines.append(f"G0 Z{fmt(safe_z)} F{args.z_feed} ; Safe height retract before tool change")
                lines.append(f"{tool} ; Tool change")
                lines.append(f"G1 E{fmt(tool_switch_prime_e)} F{tool_switch_prime_feed} ; Tool-change prime")
                lines.append("G92 E0")
                active_tool = tool
                pending_tool_switch = True

            pts = shape_points(args.shape, args.center_x, args.center_y, ring_radius, args.segments)
            if args.manual_offset_compensation:
                sx, sy = tool_compensated_xy(pts[0][0], pts[0][1], tool, args.t1_offset_x, args.t1_offset_y)
                tz = tool_compensated_z(z, tool, args.t1_offset_z)
            else:
                sx, sy = pts[0][0], pts[0][1]
                tz = z
            if pending_tool_switch:
                lines.append(f"G0 X{fmt(sx)} Y{fmt(sy)} F{args.travel_feed}")
                lines.append(f"G0 Z{fmt(tz)} F{args.z_feed} ; Lower to print height")
                pending_tool_switch = False
            else:
                lines.append(f"G0 Z{fmt(tz)} F{args.z_feed}")
                lines.append(f"G0 X{fmt(sx)} Y{fmt(sy)} F{args.travel_feed}")

            e_total = FIXED_START_EXTRUSION
            for x, y in pts[1:]:
                if args.manual_offset_compensation:
                    tx, ty = tool_compensated_xy(x, y, tool, args.t1_offset_x, args.t1_offset_y)
                else:
                    tx, ty = x, y
                lines.append(f"G1 X{fmt(tx)} Y{fmt(ty)} E{fmt(e_total)} F{args.print_feed}")
                e_total += args.edge_e

    lines.extend(
        [
            "; --- End ---",
            "G92 E0",
            "G0 Z30 F600",
            "M106 S0",
            "M84",
        ]
    )
    return lines


def main() -> None:
    args = collect_inputs()
    gcode = build_gcode(args)
    args.output.write_text("\n".join(gcode) + "\n", encoding="utf-8")
    print(f"Wrote {args.output.resolve()}")


if __name__ == "__main__":
    main()
