# WiFi Motion Detector

Detect human motion in a room using **only your laptop's existing WiFi** — no camera ,  
no extra hardware, no purchases. The app watches your link to the router and flags
**MOVEMENT** when someone moves through the space, **ROOM QUIET** when it's still.

```
+--------------------- WiFi Motion Detector ---------------------+
|         BHARTI_HOME   RSSI -71 dBm (50%)   Rx 140 Mbps         |
|                                                                |
|                        MOVEMENT DETECTED                       |
|                                                                |
|               [####################|#######] 100%             |
|            Movement is disturbing the WiFi signal.             |
|                          - details -                           |
|            score  5.40    T_high 3.20   T_low 2.30             |
|         signal ######   rtt_std ########   loss ######         |
+- keep the laptop still (it is the sensor)  |  Ctrl-C to quit --+
```

## Why this exists
Proof that "sensing through the air" works with devices you already own. Your laptop is
constantly measuring its radio link to the router; a body moving between them disturbs
those radio waves. We turn that disturbance into a live, demoable motion readout — pure
Python, zero cost.

## How it works (plain language)
1. **Sense (zero hardware).** Each second we read the link from `netsh wlan show interfaces`
   (signal strength, Signal %, adaptive Rx/Tx rate) and ping the router for round-trip
   time + packet loss. Several weak motion cues, all free.
2. **Features.** Over a sliding window we compute each cue's *level* and its *wobble*
   (rolling standard deviation). Motion makes the wobble grow, rates drop, RTT spike.
3. **Calibrate.** While you hold still, we learn each cue's robust baseline — the
   **median** (center) and **MAD** (median absolute deviation = spread). Robust stats
   shrug off the odd blip.
4. **Fuse.** Each cue becomes a robust z-score `|value - center| / (1.4826*MAD)`, clamped
   so no single noisy cue dominates, then combined into one **motion score** (weighted RMS).
5. **Decide.** Thresholds are auto-tuned from your room's own calibration noise. Hysteresis
   (separate enter/exit levels) + debounce stop flicker; the baseline slowly adapts while
   QUIET so slow environmental drift doesn't cause false alarms.

## What it can & can't detect
**Detects:** whether significant human movement is disturbing the radio path between your
laptop and router.
- **One person moving** → yes; strongest when they cross the laptop↔router line.
- **Two or more moving** → easier (more disturbance = higher score), but it **cannot count
  people** — it is strictly motion / no-motion.
- **People already in the room but still** during calibration → fine; they become part of
  the quiet baseline. (Just don't move during the ~20 s calibration.)
- **Router in another room** → works for movement in/near the laptop↔router "corridor"
  (even through a wall); motion far off that line may be missed. Coverage is that corridor,
  **not the whole house**.

**Can't:** count or locate people, or work while the laptop is moving (see below).

### ⚠ Keep the laptop still
The laptop **is the sensor**. If *it* moves (carried, on your lap), the whole signal moves
and there's no way to tell that apart from someone moving in the room. **Put the laptop on a
stable surface and leave it there.** (Sensing *while you move around* is exactly what the
multi-phone v2 is for — several *stationary* phones as fixed sensors.)

## Requirements
- **Windows** (uses `netsh` and `ping`; tested on Windows 11).
- **Python 3.10+** (developed on 3.13).
- Connected to a WiFi router.

---

## 1. Setup (one time)
Open **PowerShell** in the project folder and run:

```powershell
cd E:\ancilar\wifi-motion-detector
python -m venv .venv               # create an isolated environment
.\.venv\Scripts\Activate.ps1       # activate it (prompt shows (.venv))
pip install -r requirements.txt    # install numpy, rich, pytest
```

> Use **PowerShell**, not Command Prompt. In CMD, `cd E:\...` won't switch drives and the
> `.ps1` activate script won't run — use `E:` then `.venv\Scripts\activate.bat` instead.
> If `Activate.ps1` is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## 2. Run it
```powershell
python src\main.py
```
Then:
1. **Put the laptop on a table and don't move it.** Hold still ~20 s while it calibrates
   (`Baseline ready. T_low=… T_high=…`).
2. **Sit still** → banner stays **ROOM QUIET** (green); meter below the `|` mark.
3. **Walk between your laptop and the router** → **MOVEMENT DETECTED** (red) + a beep.
4. **Stand still** → back to QUIET in ~3–4 s. Press **Ctrl-C** to quit.

> Tip: run in **Windows Terminal** for the smooth block sparkline; the classic console
> falls back to ASCII automatically (no crash, just `#` instead of `█`).

## 3. Test it

**a) Automated unit tests** (parser, features, detector, meter — no walking needed):
```powershell
pytest -q
```
Expect `... passed`.

**b) Quick bounded run** (full pipeline on real hardware, exits after N ticks):
```powershell
$env:WMD_MAX_TICKS = 8 ; python src\main.py
```

**c) The real walk-test** (the one only a human can do): run `python src\main.py` and
follow the four steps in section 2.

---

## Reading the dashboard
- **Banner** — plain status: ROOM QUIET / MOVEMENT DETECTED / CALIBRATING / WIFI DISCONNECTED.
- **Motion meter (0–100%)** — how strong the movement signal is. The `|` marks the trip point
  (~70%): below it = quiet (green), past it = motion (red).
- **details** (for tuning) — the raw `score` vs `T_high`/`T_low`, a score sparkline, and the
  per-cue z-score bars (the longest bars are what triggered it).

## Tuning
Everything lives in `src/config.py`. Most-used knobs:

| Setting | Effect |
|---|---|
| `WINDOW` | Smaller = faster reaction/reset (noisier); larger = smoother but slower. |
| `CALIBRATION_SEC` | Longer = a more representative quiet baseline. |
| `K_HIGH` / `T_MARGIN` | Raise to reduce false alarms; lower to catch subtler motion. |
| `K_LOW` | Higher = returns to QUIET sooner after motion stops. |
| `N_ENTER` / `N_EXIT` | Debounce: higher = steadier but slower to react. |
| `FUSION_WEIGHTS` | Per-cue importance. Weight up whatever moves most on *your* hardware. |
| `PING_TARGET` | Force a router IP if auto-detection fails (e.g. `"192.168.1.1"`). |
| `BEEP` | Beep on motion start (Windows). |

After any change: run `pytest` (must stay green), then re-run the walk-test.

## Project layout
```
src/
  config.py       all tunable settings
  wifi_reader.py  read + parse live netsh link stats
  pinger.py       ping the router for RTT + packet loss
  features.py     sliding-window feature extraction
  detector.py     calibration + fusion + QUIET/MOTION state machine
  dashboard.py    rich live UI (plain summary + details)
  main.py         orchestration loop
tests/            unit tests (parser, features, detector, meter)
PLAN.md           full engineering plan + detection math
PROGRESS.md       build log / current state
```

## Troubleshooting
- **"No router found"** — set `PING_TARGET` in `config.py` to your router's IP (find it with
  `ipconfig` → *Default Gateway*). It still works on WiFi cues alone.
- **Stays QUIET even when you walk** — lower `K_HIGH`/`T_MARGIN`, or raise the weight of the
  cue that moves most (watch the detail bars). Walking *across* the laptop↔router line works best.
- **Trips to MOVEMENT while you're still** — first check the laptop isn't being bumped; then
  raise `K_HIGH`/`T_MARGIN`, or re-calibrate in a quieter moment.
- **"Calibration failed - WiFi link unstable"** — you weren't connected, or the link dropped;
  reconnect and run again.
- **Garbled characters** — your console isn't UTF-8; it auto-falls back to ASCII, which is fine.

## Roadmap
- **v2 — multi-device sensing.** Stationary phones self-report RSSI via Termux; multiple links
  crisscross the room → motion **anywhere** (not just one corridor) + rough localization.
- **v3 — web dashboard.** Browser UI instead of the terminal.
- Out of scope: CSI-level sensing (needs special NICs), anything that costs money.

## License
[MIT](LICENSE).
