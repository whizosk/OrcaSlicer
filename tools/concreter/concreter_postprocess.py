#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Concreter post-processing for OrcaSlicer G-code:
- Inject Pump ON/OFF around deposition moves
- Add U axis (orientation) based on XY direction: atan2(dy, dx) in degrees
- Optional: continuous path mode (keep pump on across short travels)
"""
import argparse
import math
import re
from pathlib import Path

MOVE_RE = re.compile(r'^(G0|G1)\s', re.IGNORECASE)

def parse_axis(line: str, axis: str):
    m = re.search(rf'(?<![A-Z0-9_.-]){axis}([-+]?\d*\.?\d+)', line, re.IGNORECASE)
    return float(m.group(1)) if m else None

def has_axis(line: str, axis: str) -> bool:
    return re.search(rf'(?<![A-Z0-9_.-]){axis}[-+]?\d', line, re.IGNORECASE) is not None

def format_u(angle_deg: float) -> str:
    return f"{angle_deg:.3f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Input G-code path")
    ap.add_argument("-o", "--output", default=None, help="Output G-code path")
    ap.add_argument("--pump-on", default=";PUMP_ON", help='Pump ON G-code, supports {FLOW}')
    ap.add_argument("--pump-off", default=";PUMP_OFF", help="Pump OFF G-code")
    ap.add_argument("--flow", type=float, default=None, help="Pump flow value (RPM or L/min), used in {FLOW}")
    ap.add_argument("--u-axis", default="U", help="Axis letter for orientation (e.g., U or A)")
    ap.add_argument("--no-u", action="store_true", help="Disable U axis injection")
    ap.add_argument("--continuous", action="store_true", help="Continuous Path mode: keep pump on across short travels")
    ap.add_argument("--travel-threshold-mm", type=float, default=0.0,
                    help="If continuous mode: keep pump on when travel distance <= threshold (mm)")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output) if args.output else in_path.with_suffix(in_path.suffix + ".concreter.gcode")

    pump_on = args.pump_on
    if "{FLOW}" in pump_on:
        flow_str = "" if args.flow is None else str(args.flow)
        pump_on = pump_on.replace("{FLOW}", flow_str)

    last_x = None
    last_y = None
    last_u = None

    pump_is_on = False
    in_deposition = False

    def is_deposition_move(line: str) -> bool:
        return MOVE_RE.match(line) is not None and has_axis(line, "E")

    def xy_distance(x0, y0, x1, y1) -> float:
        if None in (x0, y0, x1, y1):
            return float("inf")
        return math.hypot(x1 - x0, y1 - y0)

    with in_path.open("r", encoding="utf-8", errors="ignore") as f_in, out_path.open("w", encoding="utf-8") as f_out:
        for raw in f_in:
            line = raw.rstrip("\n")

            x = parse_axis(line, "X")
            y = parse_axis(line, "Y")
            next_x = last_x if x is None else x
            next_y = last_y if y is None else y

            dep = is_deposition_move(line)

            if dep and not pump_is_on:
                f_out.write(pump_on + "\n")
                pump_is_on = True
                in_deposition = True

            if (not dep) and pump_is_on and in_deposition:
                if args.continuous and args.travel_threshold_mm > 0.0:
                    if MOVE_RE.match(line):
                        dist = xy_distance(last_x, last_y, next_x, next_y)
                        if dist > args.travel_threshold_mm:
                            f_out.write(args.pump_off + "\n")
                            pump_is_on = False
                            in_deposition = False
                    else:
                        f_out.write(args.pump_off + "\n")
                        pump_is_on = False
                        in_deposition = False
                else:
                    f_out.write(args.pump_off + "\n")
                    pump_is_on = False
                    in_deposition = False

            if (not args.no_u) and MOVE_RE.match(line) and (x is not None or y is not None) and (not has_axis(line, args.u_axis)):
                if last_x is not None and last_y is not None and next_x is not None and next_y is not None:
                    dx = next_x - last_x
                    dy = next_y - last_y
                    if abs(dx) > 1e-9 or abs(dy) > 1e-9:
                        last_u = math.degrees(math.atan2(dy, dx))
                if last_u is not None:
                    line = line + f" {args.u_axis}{format_u(last_u)}"

            f_out.write(line + "\n")

            if x is not None:
                last_x = x
            if y is not None:
                last_y = y

        if pump_is_on:
            f_out.write(args.pump_off + "\n")

    print(f"OK: wrote {out_path}")

if __name__ == "__main__":
    main()
