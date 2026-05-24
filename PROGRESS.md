# wifi-motion-detector — Build Log

> Where we are, newest at top. Update before ending any session.

_Last updated: 2026-05-24 — v1.1 polish (clearer UI, faster reset, usage guidance). Pending: your walk-test._

## Status
🟢 **v1 done + hardened.** Full pipeline (read → ping → features → fusion detector → live `rich`
dashboard → beep) runs end-to-end on real hardware (exit 0, calibrates, renders, no crash).
**21 unit tests green.** Full README (setup/run/test step-by-step + troubleshooting) + MIT LICENSE;
code pushed to GitHub. Engineering plan: `PLAN.md`.

## Hardening pass (2026-05-24, post-review)
- Fixed infinite-loop risk: calibration now bails with a clear error if the link drops.
- Live loop handles mid-run disconnect gracefully (NO LINK state; detection paused).
- `detector.update` computes the per-cue breakdown before drift (consistent with the score).
- Sparkline now scaled to `T_high` so motion visibly spikes above the rest line.
- Added MIT LICENSE, pinned `requirements.txt`, added a baseline-drift unit test.

## v1.1 polish from real-use feedback (2026-05-24)
Decisions: polish v1 now, phones (v2) next · interface = plain summary + details · reaction = balanced.
- **Faster reaction/reset:** `WINDOW` 8→5, `N_EXIT` 3→2 (clears in ~3-4 s vs ~8-10 s).
- **Glanceable UI:** plain banner (ROOM QUIET / MOVEMENT DETECTED), 0-100% motion meter with a
  trip marker; technical z-score details kept below. New `motion_level()` + 4 tests (21 total).
- **Usage guidance:** startup tip + README "What it can & can't detect" + "keep the laptop still".
- **Defined limits (honest):** single link detects motion in the laptop↔router corridor only;
  can't count/locate people; laptop must stay stationary (the sensor mustn't move).
- **Next:** A4 walk-test by user, then Phase B (v2 multi-phone: Termux RSSI → hub → per-link
  detection + rough localization). Termux `termux-wifi-connectioninfo` confirmed feasible.
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
