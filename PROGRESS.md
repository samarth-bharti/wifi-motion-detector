# wifi-motion-detector — Build Log

> Where we are, newest at top. Update before ending any session.

_Last updated: 2026-05-24 — v1 complete: all 5 stages built, tested, pushed. Pending: your live walk-test._

## Status
🟢 **v1 done.** Full pipeline (read → ping → features → fusion detector → live `rich` dashboard
→ beep) runs end-to-end on real hardware (exit 0, calibrates, renders, no crash). **16 unit tests
green.** README complete; code pushed to GitHub. Engineering plan: `PLAN.md`.
**Only open item:** the physical walk-test (CLEAR→MOTION when you walk) — that needs a human; run
`python src/main.py` and confirm. Tune `K_HIGH`/`T_MARGIN`/`FUSION_WEIGHTS` in `config.py` if needed.

## Decisions (2026-05-24)
- **Scope = full sensor fusion**: RSSI + Signal% + adaptive Rx/Tx rate + ping RTT/loss → one score.
- **Tuning = balanced + auto-tuned**: thresholds from baseline noise + a percentile floor;
  hysteresis + debounce to avoid flicker.

## Findings from live testing
- On this MediaTek card the **`Rssi` field is sticky** (pinned -71); **`Signal %` is the lively
  cue** (swings ~39–57% at rest). Fusion handles this by weighting on real variance.
- First auto-threshold (MAD-of-scores) sat inside the at-rest noise → false trips. Fixed by also
  anchoring `T_high` to the 90th-percentile of at-rest scores × `T_MARGIN`. At-rest now stays CLEAR.
- Unicode block chars crash on legacy `cp1252` consoles → dashboard + console messages use an
  ASCII fallback (auto-detected).
- Baselines observed across runs: `T_high` ~3.2–5.4 depending on ambient jitter (auto-tuned).

## Confirmed
- `netsh` live: `Rssi -71` / `Signal 54%`, Rx 162 / Tx 52 Mbps to `BHARTI_HOME`, 2.4 GHz, ch 11.
- Router (gateway) auto-detected: `192.168.1.1`. Ping RTT ~5–6 ms at rest, 0% loss.
- Stack: Python 3.13.4 + numpy 2.4 + rich 15 + pytest 9.

## Stages (see PLAN.md for detail)
- [x] Stage 0 — workspace + git + GitHub + continuity files
- [x] Stage 1 — sensing core: `config.py` + `wifi_reader.py` (3 tests)
- [x] Stage 2 — second sense + features: `pinger.py` + `features.py` (+8 tests)
- [x] Stage 3 — fusion detector: `detector.py` (+5 tests; calibration, score, hysteresis, drift)
- [x] Stage 4 — dashboard + glue: `dashboard.py` + `main.py` (renders + runs end-to-end)
- [x] Stage 5 — polish + full README + push to GitHub

## How to run / test
- Run: `.\.venv\Scripts\Activate.ps1` ; `python src/main.py`  (hold still ~20s, then walk)
- Tests: `pytest`   ·   Bounded demo: `$env:WMD_MAX_TICKS=8; python src/main.py`

## Open questions
- Walk-test result on this link (does walking push score above T_high?) — to be confirmed by you.
- v2: phones via Termux for multi-link + rough localization.
