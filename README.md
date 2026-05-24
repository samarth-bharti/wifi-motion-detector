# WiFi Motion Detector

Detect human motion in a room using **only your laptop's existing WiFi** — no camera,
no extra hardware, no purchases. The app watches your link to the router and flags
**MOTION** when someone moves through the space, **CLEAR** when the room is still.

```
+--------------------- WiFi Motion Detector ---------------------+
|         BHARTI_HOME   RSSI -71 dBm (50%)   Rx 140 Mbps         |
|                                                                |
|                             MOTION                             |
|                                                                |
|            score  5.37    T_high 3.20   T_low 2.30             |
|              ▁▁▂▁▂▁▃▂▁▂▆█▇█▆▅▃▂▁▁▂▁▁▂▁▁▁▁▁▁▁▁                  |
|                                                                |
|                   signal ██████ 2.0                            |
|               signal_std ████████████ 4.1                      |
|                 rssi_std  0.0                                  |
|                  rx_rate ██ 0.6                                |
|                      rtt ████████ 2.8                          |
|                  rtt_std ████████████ 4.0                      |
|                     loss ██████ 2.0                            |
+------------------------ Ctrl-C to stop ------------------------+
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
   CLEAR so slow environmental drift doesn't cause false alarms.

The dashboard's per-cue bars show *which* signals drove a detection — so it's legible,
not a black box.

## Requirements
- **Windows** (uses `netsh` and `ping`; tested on Windows 11).
- **Python 3.10+** (developed on 3.13).
- Connected to a WiFi router.

---

## 1. Setup (one time)
Open PowerShell in the project folder and run:

```powershell
cd E:\ancilar\wifi-motion-detector
python -m venv .venv               # create an isolated environment
.\.venv\Scripts\Activate.ps1       # activate it (prompt shows (.venv))
pip install -r requirements.txt    # install numpy, rich, pytest
```

> If `Activate.ps1` is blocked, allow scripts for your user once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 2. Run it
```powershell
python src/main.py
```
Then:
1. **Hold still ~20 s** while it calibrates. It prints `Baseline ready. T_low=… T_high=…`.
2. **Sit still** → the banner stays **CLEAR** (green); score below `T_high`.
3. **Walk between your laptop and the router** → it flips to **MOTION** (red) and beeps.
4. **Stand still** → back to **CLEAR** after a few seconds. Press **Ctrl-C** to quit.

> Tip: run in **Windows Terminal** for the smooth block sparkline; the classic console
> falls back to ASCII automatically (no crash, just `#` instead of `█`).

## 3. Test it

**a) Automated unit tests** (parser, features, detector logic — no walking needed):
```powershell
pytest -q
```
Expect `... passed`. These prove the netsh/ping parsing, the rolling-window math, and the
CLEAR↔MOTION state machine (including debounce and drift).

**b) Quick bounded run** (full pipeline on real hardware, exits after N ticks):
```powershell
$env:WMD_MAX_TICKS = 8 ; python src/main.py
```

**c) The real walk-test** (the one only a human can do):
Run `python src/main.py`, then follow the four steps in section 2. You should see:
- still room → **CLEAR**, score comfortably under `T_high`;
- you walking the laptop↔router path → **MOTION**;
- you stop → **CLEAR** again.

If it's too jumpy or too sluggish, tune it (next section) and re-test.

---

## Reading the dashboard
- **Banner** — current state: CLEAR / MOTION / CALIBRATING / NO LINK.
- **score** — the fused motion score; compare against **T_high** (enter) and **T_low** (exit).
- **sparkline** — recent scores, scaled so `T_high` sits about two-thirds up; motion clearly
  spikes above the rest line.
- **per-cue bars** — each feature's z-score this tick; the longest bars are what triggered it.

## Tuning
Everything lives in `src/config.py`. Most-used knobs:

| Setting | Effect |
|---|---|
| `CALIBRATION_SEC` | Longer = a more representative quiet baseline. |
| `K_HIGH` / `T_MARGIN` | Raise to reduce false alarms; lower to catch subtler motion. |
| `K_LOW` | Higher = returns to CLEAR sooner after motion stops. |
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
  detector.py     calibration + fusion + CLEAR/MOTION state machine
  dashboard.py    rich live UI
  main.py         orchestration loop
tests/            unit tests (parser, features, detector)
PLAN.md           full engineering plan + detection math
PROGRESS.md       build log / current state
```

## Troubleshooting
- **"No router found"** — auto-detection failed; set `PING_TARGET` in `config.py` to your
  router's IP (find it with `ipconfig` → *Default Gateway*). It still works on WiFi cues alone.
- **Stays CLEAR even when you walk** — lower `K_HIGH`/`T_MARGIN`, or raise the weight of the
  cue that moves most (watch the bars). Walking *across* the laptop↔router line works best.
- **Trips to MOTION while you're still** — raise `K_HIGH`/`T_MARGIN`, or re-calibrate in a
  quieter moment (don't move during the ~20 s calibration).
- **"Calibration failed - WiFi link unstable"** — you weren't connected, or the link dropped;
  reconnect and run again.
- **Garbled characters** — your console isn't UTF-8; it auto-falls back to ASCII, which is fine.

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
[MIT](LICENSE).
