# wifi-motion-detector — Engineering Plan (v1, full-fusion)

> The detailed, end-to-end build plan. Spec lives in `task.md`; live status in `PROGRESS.md`.
> Decisions (2026-05-24): **Scope = full sensor fusion now**; **Tuning = balanced + auto-tuned**.

## Context — why this plan
The original v1 idea was a single RSSI stream from `netsh`. But `netsh wlan show interfaces`
on this laptop also reports **Signal %**, and the **adaptive Rx/Tx rates** — and we can add a
**continuous ping to the router** for RTT + packet-loss. All of that is still *zero extra
hardware*. Fusing several weak motion cues into one score gives noticeably better, steadier
detection than RSSI alone, while staying pure Python. That is what "best results, no hardware"
means here.

## The signals we get for free (verified live)
From `netsh wlan show interfaces` (~1 Hz):
- **Rssi** (dBm, e.g. `-71`) — primary signal strength. Finer than Signal %.
- **Signal** (%, e.g. `54%`) — quantized RSSI; fallback if Rssi line is absent.
- **Receive rate / Transmit rate** (Mbps) — the card's *adaptive* link speed; drops when a
  body degrades the channel.
From pinging the default gateway (the router) continuously:
- **RTT** (ms) — round-trip time; motion → retransmissions → RTT spikes.
- **Packet loss** — fraction lost in the recent window; motion → more loss.
(Pinging also keeps the link "warm" so RSSI/rate keep updating.)

## How detection works (plain language)
**Per tick (~1/sec) we build a feature vector:**
1. RSSI (dBm)            4. Ping RTT (ms)
2. RSSI *wobble* = rolling std of recent RSSI   5. RTT *wobble* = rolling std of recent RTT
3. Rx/Tx rate (+ their change) 6. Packet-loss fraction (window)
Motion shows up as bigger *wobble*, rate drops, RTT spikes, and loss — usually several at once.

**Calibration (quiet baseline, ~20–30 s):** for each feature store a **robust center =
median** and **robust spread = MAD** (median absolute deviation). Robust stats so one stray
blip doesn't poison the baseline (median/MAD ignore outliers; mean/std don't).

**Live motion score:** per feature, `z = |value − center| / (1.4826·MAD + ε)`
(the 1.4826 makes MAD comparable to a standard deviation). Combine the z's into one score via a
**weighted RMS** (config weights — RSSI/RTT wobble + loss weigh most; raw rate least) so several
mild cues add up but no single noisy feature dominates.

**Auto-tuned thresholds (the "balanced" choice):** from the calibration scores' own median+MAD
set `T_high = cal_med + k_high·cal_mad` (enter MOTION) and `T_low = cal_med + k_low·cal_mad`
(return to CLEAR), with `T_low < T_high`. Tuned to *this* room, not hard-coded guesses.

**Hysteresis + debounce:** declare MOTION only after `N_enter` consecutive samples above
`T_high`; return to CLEAR only after `N_exit` consecutive below `T_low`. Kills flicker.

**Adaptive baseline drift:** while CLEAR and stable, nudge each center/spread toward recent
values with a slow EWMA (`alpha≈0.02`); freeze while in MOTION. Tracks slow environmental
change (temperature, router power-save) without chasing real motion.

## Module layout (each file < 150 lines, single responsibility)
- `src/config.py`     — all tunables (intervals, window sizes, weights, k_high/k_low, debounce,
                        EWMA alpha, ping target/auto, calibration length).
- `src/wifi_reader.py`— run + parse `netsh` → `WifiSample(rssi, signal_pct, rx_rate, tx_rate,
                        ssid, bssid)`; robust to missing fields; helper to find gateway IP.
- `src/pinger.py`     — ping the gateway once per tick (short timeout) → `(rtt_ms | None)`;
                        None = lost packet.
- `src/features.py`   — sliding-window buffers; turn recent samples into the feature vector
                        (rolling std of RSSI/RTT, rate change, loss fraction).
- `src/detector.py`   — calibration (median/MAD), fusion → score, auto threshold, hysteresis
                        state machine, adaptive drift. `update(features) -> (state, score, parts)`.
- `src/dashboard.py`  — `rich` live UI: header (SSID/RSSI), RSSI + score sparklines, per-feature
                        contribution bars, big CLEAR/MOTION banner, calibration progress.
- `src/main.py`       — orchestration: setup → calibrate → live loop (read+ping → features →
                        detector → dashboard → beep on MOTION) → clean Ctrl-C exit.
- `tests/`            — `test_wifi_reader.py` (parse real + degraded netsh text, Signal% fallback),
                        `test_features.py` (rolling-stat correctness), `test_detector.py`
                        (synthetic streams: flat→CLEAR, injected wobble/RTT→MOTION, no flicker).

## Build stages (small, runnable, tested — approval between each)
- [ ] **Stage 1 — Sensing core.** `config.py` + `wifi_reader.py` + a tiny live printout of
      RSSI/Signal/rates. Test the parser. *See it:* numbers updating once/sec.
- [ ] **Stage 2 — Second sense + features.** `pinger.py` (gateway RTT/loss) + `features.py`
      (sliding windows, rolling stats). *See it:* live feature vector printed. Test features.
- [ ] **Stage 3 — Fusion detector.** `detector.py`: calibration, fused score, auto thresholds,
      hysteresis, drift. *See it:* text loop printing score + CLEAR/MOTION. Test detector.
- [ ] **Stage 4 — Dashboard + glue.** `dashboard.py` + `main.py`: the polished `rich` demo +
      beep. *See it:* the real product.
- [ ] **Stage 5 — Polish + ship.** Tests green, README (run / how-it-works / extend / v2-v3),
      update `PROGRESS.md`, push to GitHub.

## Verification (done-when)
1. `pytest` green (parser + features + detector on synthetic data).
2. `python src/main.py` calibrates while you hold still, then flips to **MOTION** when you walk
   between laptop and router and back to **CLEAR** when still — steadily, without flicker.
3. The dashboard looks clean enough to demo.
4. Pushed to the public repo with the README.

## Roadmap beyond v1 (unchanged, out of scope now)
v2 = multi-device sensing (phones self-report RSSI via Termux) → enables rough localization.
v3 = web/browser dashboard. CSI-level sensing needs special NICs — out of scope.
