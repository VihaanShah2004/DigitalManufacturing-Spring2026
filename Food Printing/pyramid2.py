import math
from pathlib import Path
from types import SimpleNamespace


def fmt(value: float) -> str:
    return f"{value:.2f}"


def collect_inputs() -> SimpleNamespace:
    print("Pyramid G-code generator")
    print("Enter a value for each question, or press Enter to use the default.")

    # Keep advanced machine settings fixed for simplicity.
    fan_speed = 255
    travel_feed = 1200
    z_feed = 600
    prime_travel_z = 10.0
    prime_x = 20.0
    prime_y = 20.0
    prime_z = 5.0
    prime_line_length = 15.0
    prime_feed = 400
    prime_e = 1.2
    prime_dwell_ms = 1000
    retract_feed = 1200
    final_z = 45.0
    retract_e = 75.0

    output_raw = input("Output file name [pyramid3.gcode]: ").strip()
    output_name = output_raw if output_raw else "pyramid3.gcode"
    layers = int(input("Number of layers [13]: ").strip() or 13)
    default_switch_layer = max(1, layers // 2)

    return SimpleNamespace(
        output=Path(output_name),
        layers=layers,
        layer_height=float(input("Layer height in mm [1.0]: ").strip() or 1.0),
        start_z=float(input("Start Z in mm [5.0]: ").strip() or 5.0),
        start_size=float(input("Layer 1 triangle size in mm [30.0]: ").strip() or 30.0),
        size_decrement=float(input("Base size decrease per layer in mm [0.5]: ").strip() or 0.5),
        center_x=float(input("Center X [55.0]: ").strip() or 55.0),
        center_y=float(input("Center Y [49.0]: ").strip() or 49.0),
        twist_step_deg=1.5,
        fan_speed=fan_speed,
        travel_feed=travel_feed,
        z_feed=z_feed,
        first_layer_feed=int(input("Layer 1 print feed [750]: ").strip() or 750),
        feed_step=int(input("Feed increase per layer [100]: ").strip() or 100),
        max_print_feed=int(input("Maximum print feed [1100]: ").strip() or 1100),
        prime_travel_z=prime_travel_z,
        prime_x=prime_x,
        prime_y=prime_y,
        prime_z=prime_z,
        prime_line_length=prime_line_length,
        prime_feed=prime_feed,
        prime_e=prime_e,
        prime_dwell_ms=prime_dwell_ms,
        first_layer_edge_e=float(input("Layer 1 edge extrusion [1.8]: ").strip() or 1.8),
        layer_edge_e_drop=float(input("Edge extrusion drop per layer [0.03]: ").strip() or 0.03),
        switch_layer=int(
            input(f"Layer to switch material after (0 = no switch) [{default_switch_layer}]: ").strip()
            or default_switch_layer
        ),
        mold_offset_x=float(input("Second mold X offset in mm [0.0]: ").strip() or 0.0),
        mold_offset_y=float(input("Second mold Y offset in mm [0.0]: ").strip() or 0.0),
        retract_feed=retract_feed,
        final_z=final_z,
        retract_e=retract_e,
    )


def triangle_vertices(cx: float, cy: float, size: float, angle_deg: float) -> list[tuple[float, float]]:
    radius = size / math.sqrt(3.0)
    vertices = []
    for i in range(3):
        angle = math.radians(angle_deg + (i * 120.0))
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        vertices.append((x, y))
    return vertices


def build_gcode(args: SimpleNamespace) -> list[str]:
    lines: list[str] = [
        "The Code:",
        "; --- START SKELETON ---",
        f"M106 S{args.fan_speed}; Fans max",
        "G21 G90 G92 E0 M82",
        "; --- PRESSURE PRIME ---",
        f"G0 Z{args.prime_travel_z:g} F{args.z_feed}",
        f"G0 X{args.prime_x:g} Y{args.prime_y:g}",
        f"G1 Z{args.prime_z:.1f} F500",
        f"G1 X{args.prime_x + args.prime_line_length:g} Y{args.prime_y:g} E{args.prime_e:g} F{args.prime_feed}",
        f"G4 P{args.prime_dwell_ms}",
        f"G0 Z{args.prime_travel_z:g} F{args.z_feed}",
    ]

    e_total = args.prime_e
    current_size = args.start_size
    center_offset_x = 0.0
    center_offset_y = 0.0

    for layer_idx in range(args.layers):
        layer_number = layer_idx + 1
        if args.switch_layer > 0 and layer_number == args.switch_layer + 1:
            lines.append("; --- MATERIAL SWITCH ---")
            lines.append(f"G0 Z{args.prime_travel_z:g} F{args.z_feed} ; Lift before switching")
            lines.append("M0 ; Change material / move to second injector")
            center_offset_x = args.mold_offset_x
            center_offset_y = args.mold_offset_y

        angle = layer_idx * args.twist_step_deg
        z = args.start_z + (layer_idx * args.layer_height)
        edge_e = max(0.01, args.first_layer_edge_e - (layer_idx * args.layer_edge_e_drop))
        feed = min(args.max_print_feed, args.first_layer_feed + (layer_idx * args.feed_step))
        if layer_idx > 0:
            extrusion_scale = edge_e / args.first_layer_edge_e if args.first_layer_edge_e > 0 else 1.0
            current_size -= args.size_decrement * extrusion_scale
        size = current_size
        center_x = args.center_x + center_offset_x
        center_y = args.center_y + center_offset_y
        v1, v2, v3 = triangle_vertices(center_x, center_y, size, angle)

        lines.append(f"; --- LAYER {layer_number}: {size:.1f}mm | {angle:.1f}\N{DEGREE SIGN} | Z{z:.1f} ---")
        if layer_idx == 0:
            lines.append(f"G0 X{fmt(v1[0]).rstrip('0').rstrip('.')} Y{fmt(v1[1]).rstrip('0').rstrip('.')} F{args.travel_feed}")
            lines.append(f"G1 Z{z:.1f} F500")
        else:
            lines.append(f"G0 Z{z:.1f} F{args.z_feed}")
            lines.append(f"G0 X{fmt(v1[0])} Y{fmt(v1[1])}")

        e_total += edge_e
        lines.append(f"G1 X{fmt(v2[0])} Y{fmt(v2[1])} E{e_total:.2f} F{feed} ; Increment: {edge_e:.2f}")
        e_total += edge_e
        lines.append(f"G1 X{fmt(v3[0])} Y{fmt(v3[1])} E{e_total:.2f} F{feed}")
        e_total += edge_e
        lines.append(f"G1 X{fmt(v1[0])} Y{fmt(v1[1])} E{e_total:.2f} F{feed}")

    lines.extend(
        [
            "; --- FINAL CLEANUP ---",
            f"G1 E{args.retract_e:.2f} F{args.retract_feed} ; Retract 1.8mm",
            f"G0 Z{args.final_z:g} F{args.z_feed} ; Finish high",
            "M84",
            "M106 S0",
        ]
    )
    return lines


def main() -> None:
    args = collect_inputs()
    gcode_lines = build_gcode(args)
    args.output.write_text("\n".join(gcode_lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
