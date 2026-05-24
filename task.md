# wifi-motion-detector — Spec (v1)

## Goal
Detect human motion in a room using only a laptop's existing WiFi connection — no camera,
no extra hardware, no purchases. Show a clear, demoable live readout that flips between
CLEAR and MOTION as someone moves through the laptop↔router signal path.

## Why
Proof that "sensing through the air" is possible with devices you already own. A real,
usable, show-it-to-people product — not a mockup.

## Approach
- Poll WiFi signal strength (RSSI, dBm) ~once/sec via `netsh wlan show interfaces`.
- Calibrate a "quiet room" baseline (mean + normal jitter).
- Flag MOTION when live signal deviates beyond baseline jitter, with debounce to avoid
  flicker. Tune sensitivity from the measured baseline noise.
- Present a clean live terminal dashboard (signal graph + big CLEAR/MOTION status).

## Constraints
- Pure Python; libraries OK (numpy, rich), but no special hardware / no paid services.
- Files modular, < 150 lines each.
- Build in tested, approved stages.

## Out of scope (v1)
- Multi-phone sensing (v2 — Android via Termux).
- Web/browser dashboard (v3).
- CSI-level / specialized-hardware sensing.
- Rough localization (needs multiple links → v2).

## Done when
- `python src/main.py` calibrates, then reliably shows MOTION when a person walks between
  laptop and router and returns to CLEAR when still.
- The display looks clean enough to demo proudly.
- `pytest` passes (parser + detector).
- Code pushed to a public GitHub repo with a README (run / how-it-works / extend / v2).

## Verification
1. Run it; stay still during calibration.
2. Walk between laptop and router → status → MOTION.
3. Step away / hold still → status → CLEAR.
4. `pytest` green.
