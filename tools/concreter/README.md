# Concreter tools (OrcaSlicer fork)

This folder contains a simple post-processing script to make exported G-code usable for concrete printing.

## What it does
- Injects Pump ON before deposition moves and Pump OFF after deposition moves
- Adds an orientation axis (default: U) based on XY motion direction:
  U = atan2(dY, dX) in degrees
- Optional "Continuous Path mode": keeps the pump ON across short travels

## Requirements
- Python 3.12+ (Windows: use `py` launcher)

## Usage
From the OrcaSlicer repo root:

```powershell
py tools\concreter\concreter_postprocess.py input.gcode `
  --pump-on "M3 S{FLOW}" --pump-off "M5" --flow 120 `
  --u-axis U --continuous --travel-threshold-mm 2.0
```

Output:
- `input.gcode.concreter.gcode` (unless `--output` is provided)

## Parameters
- `--pump-on`: Pump ON G-code. Supports `{FLOW}` placeholder.
- `--pump-off`: Pump OFF G-code.
- `--flow`: Value substituted into `{FLOW}` (RPM or L/min, depending on your firmware).
- `--u-axis`: Axis letter for orientation (U, A, etc.).
- `--continuous`: Enables Continuous Path mode.
- `--travel-threshold-mm`: Keeps pump ON for travel moves shorter than this distance.

## Notes
- Deposition detection currently uses presence of `E` in a `G0/G1` line.
  If your workflow does not output `E`, adjust detection logic accordingly.
