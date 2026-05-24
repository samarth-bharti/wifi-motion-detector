"""Tunable settings for wifi-motion-detector — one place for every knob.

Grows per build stage. Stage 1 only needs sampling settings; detection/ping
knobs are added in later stages. All times in seconds unless noted.
"""

# --- Sampling -------------------------------------------------------------
SAMPLE_INTERVAL_SEC = 1.0   # netsh refreshes RSSI ~once/sec — no point polling faster
NETSH_TIMEOUT_SEC = 5.0     # give up on a single netsh call after this long

# --- Pinging the router (Stage 2) -----------------------------------------
PING_TARGET = None      # None = auto-detect the default gateway (your router)
PING_TIMEOUT_MS = 800   # a ping with no reply in this long counts as a lost packet

# --- Sliding window (Stage 2) ---------------------------------------------
WINDOW = 8              # samples kept for rolling stats (~8 s of history)

# --- Detection / fusion (Stage 3) -----------------------------------------
CALIBRATION_SEC = 20    # seconds of "hold still" used to learn the quiet baseline

# Which features feed the motion score. Raw 'rssi' is excluded (sticky on this
# card); its wobble 'rssi_std' is kept and simply contributes ~0 when flat.
FUSION_FEATURES = ["signal", "signal_std", "rssi_std", "rx_rate",
                   "rtt", "rtt_std", "loss"]

# Per-feature weight in the fused score (noisy-at-rest features weigh less).
FUSION_WEIGHTS = {
    "signal": 1.0, "signal_std": 1.5, "rssi_std": 1.0, "rx_rate": 0.5,
    "rtt": 0.8, "rtt_std": 1.2, "loss": 1.5,
}

K_HIGH = 3.0            # enter MOTION above baseline_score + K_HIGH * noise
K_LOW = 1.6            # return to CLEAR below baseline_score + K_LOW * noise (hysteresis)
T_HIGH_PCTL = 90        # T_high must clear this percentile of at-rest scores...
T_MARGIN = 1.3         # ...by at least this multiple (keeps it above normal jitter)
N_ENTER = 2            # consecutive samples above T_high before declaring MOTION (debounce)
N_EXIT = 3            # consecutive samples below T_low before returning to CLEAR
Z_CAP = 6.0            # clamp any single feature's z-score so none can dominate
DRIFT_ALPHA = 0.02     # how fast the baseline adapts while calmly CLEAR (0 = never)
EPS = 1e-6            # guards against divide-by-zero when a feature never moves

# --- Dashboard (Stage 4) --------------------------------------------------
BEEP = True            # beep once when motion starts (Windows winsound)
DASHBOARD_FPS = 4      # how often the live UI repaints per second
