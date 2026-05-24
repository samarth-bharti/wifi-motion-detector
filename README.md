# WiFi Motion Detector

Detect motion in a room using **only your laptop's WiFi** — no camera, no extra hardware.
It watches the WiFi signal strength to your router; when someone moves through the space,
the signal changes, and the app flags **MOTION**.

> 🚧 v1 in active development — see `PROGRESS.md` for status and `task.md` for the spec.

## Quick start (Windows)

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python src/main.py

## How it works
1. Reads WiFi signal strength (RSSI, in dBm) ~once/sec via `netsh wlan show interfaces`.
2. Learns a "quiet room" baseline (average signal + its normal jitter).
3. Flags **MOTION** when the live signal deviates beyond that normal jitter.

Full docs (how to extend, the v2 multi-phone roadmap) arrive at Stage 4.
