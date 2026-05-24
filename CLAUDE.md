# wifi-motion-detector — Project Guide (read first)

## What this is
A WiFi-based motion detector that needs **zero extra hardware**. It watches the laptop's
WiFi signal strength (RSSI, in dBm) to the home router; when a person moves through the
space, the signal wobbles beyond its normal jitter → we flag **MOTION**. Pure Python.
v1 = laptop-only. Full spec: `task.md`. Current state: `PROGRESS.md`.

## How we work together (the owner's rules — follow exactly)
- Build in **small stages** the owner can see and react to.
- **Explain what and why as you go** — this is also a learning project.
- **Show the plan and get approval before building** each stage.
- If you hit a problem, **give options**, don't silently pick one.
- Keep files **clean, modular, under 150 lines each**.
- **Test each stage** before moving to the next.
- **No jargon without a plain-language explanation.**

## Stack
Python 3.13 · numpy (stats) · rich (terminal UI) · winsound (beep, stdlib) · pytest.
Windows: signal read via `netsh wlan show interfaces` (parses the `Rssi` line, in dBm).

## Run / test
- Activate venv: `.\.venv\Scripts\Activate.ps1`
- Run: `python src/main.py`
- Tests: `pytest`

## Layout
- `src/wifi_reader.py` — read & parse live RSSI
- `src/detector.py` — baseline calibration + motion detection
- `src/dashboard.py` — rich live UI
- `src/main.py` — orchestration loop
- `src/config.py` — tunable settings
- `tests/` — unit tests

## Gotchas
- Laptop reads **only its own** link to the router (the Windows WiFi card can't sniff
  other devices). Multi-phone sensing (v2) needs each phone to self-report via Termux.
- `netsh` refreshes RSSI roughly **once per second** → detects walking, not fine gestures.
- Detection is environment-sensitive → always calibrate a quiet baseline first.

## Out of scope (v1)
Multi-phone (v2), web dashboard (v3), special CSI hardware, anything that costs money.
