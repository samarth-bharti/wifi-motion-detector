# WiFi Motion Detector

Detect human motion in a room using **only your laptop's existing WiFi** — no camera,
no extra hardware, no purchases. The app watches your link to the router and flags
**MOTION** when someone moves through the space, **CLEAR** when the room is still.

```
+--------------------- WiFi Motion Detector ---------------------+
|         BHARTI_HOME   RSSI -71 dBm (50%)   Rx 140 Mbps         |
|                              MOTION                            |
|            score  5.37    T_high 3.20   T_low 2.30             |
|                   signal  ######  signal_std  ########         |
|                      rtt  #####    rtt_std     ######          |
+------------------------ Ctrl-C to stop ------------------------+
```

## Why this exists
Proof that "sensing through the air" works with devices you already own. Your laptop is
constantly measuring its radio link to the router; a body moving between them disturbs
those radio waves. We turn that disturbance into a live, demoable motion readout — pure
Python, zero cost.

## How it works
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
   CLEAR so slow environmental drift doesn't cause false alarms.

The dashboard's per-feature bars show *which* cues drove a detection — so it's legible,
not a black box.

## Quick start (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/main.py
```

Then:
1. **Hold still ~20 s** while it calibrates.
2. **Sit still** → stays **CLEAR**.
3. **Walk between your laptop and the router** → flips to **MOTION** (+ a beep).
4. **Stand still** → back to **CLEAR**. `Ctrl-C` to quit.

> Tip: run in **Windows Terminal** for the smooth block sparkline; the classic console
> falls back to ASCII automatically.

## Tuning
Everything lives in `src/config.py`. The knobs you'll touch most:

| Setting | Effect |
|---|---|
| `CALIBRATION_SEC` | Longer = a more representative quiet baseline. |
| `K_HIGH` / `T_MARGIN` | Raise to reduce false alarms; lower to catch subtler motion. |
| `K_LOW` | Lower = returns to CLEAR sooner after motion stops. |
| `N_ENTER` / `N_EXIT` | Debounce: higher = steadier but slower to react. |
| `FUSION_WEIGHTS` | Per-cue importance. Weight up whatever moves most on *your* hardware. |
| `BEEP` | Beep on motion start (Windows). |

## Testing

```powershell
pytest                                  # unit tests (parser + features + detector)
$env:WMD_MAX_TICKS = 8; python src/main.py   # run a fixed number of ticks then exit
```

## Project layout
```
src/
  config.py       all tunable settings
  wifi_reader.py  read + parse live netsh link stats
  pinger.py       ping the router for RTT + packet loss
  features.py     sliding-window feature extraction
  detector.py     calibration + fusion + CLEAR/MOTION state machine
  dashboard.py    rich live UI
  main.py         orchestration loop
tests/            unit tests
PLAN.md           full engineering plan + detection math
PROGRESS.md       build log / current state
```

## Honest limitations
- The laptop reads **only its own** link to the router — it can't sense other devices.
- `netsh` refreshes ~once per second, so this detects **walking, not fine gestures**.
- Detection is environment-sensitive — **always calibrate a quiet baseline** first.
- On some WiFi cards the `Rssi` field is coarse/sticky; the fusion approach compensates by
  leaning on whichever cues actually move (here, Signal % and ping RTT).

## Roadmap
- **v2 — multi-device sensing.** Phones self-report RSSI via Termux; multiple links enable
  rough localization (which part of the room).
- **v3 — web dashboard.** Browser UI instead of the terminal.
- Out of scope: CSI-level sensing (needs special NICs), anything that costs money.

## License
MIT.
