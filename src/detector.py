"""Fusion motion detector — turns the feature vector into CLEAR / MOTION.

How it works (plain language):
1. Calibrate: while you hold still, learn each feature's robust 'center' (median)
   and 'spread' (MAD = median absolute deviation). Robust stats ignore stray blips.
2. Score: for each feature, z = |value - center| / (1.4826*spread). The 1.4826
   makes MAD comparable to a standard deviation. We clamp z (Z_CAP) so no single
   noisy feature can dominate, then combine into one score via a weighted RMS.
3. Thresholds: from the calibration scores' own median+spread we auto-derive
   T_high (enter MOTION) and a lower T_low (return to CLEAR) — tuned to your room.
4. State: need N_ENTER samples above T_high to flip to MOTION, N_EXIT below T_low
   to flip back (hysteresis + debounce kill flicker).
5. Drift: while calmly CLEAR, nudge the baseline toward recent values so slow
   environmental change doesn't cause false alarms. Frozen during MOTION.
"""
from __future__ import annotations

import math

import numpy as np

import config


class Detector:
    def __init__(self):
        self.baseline: dict[str, tuple[float, float]] = {}  # feature -> (center, spread)
        self.t_high: float = 0.0
        self.t_low: float = 0.0
        self.state: str = "CALIBRATING"
        self._enter = 0
        self._exit = 0

    def calibrate(self, feature_dicts: list[dict]) -> None:
        for k in config.FUSION_FEATURES:
            arr = np.array([fd[k] for fd in feature_dicts], dtype=float)
            center = float(np.median(arr))
            spread = float(np.median(np.abs(arr - center)))
            self.baseline[k] = (center, spread)

        scores = np.array([self._score(fd) for fd in feature_dicts])
        cmed = float(np.median(scores))
        cspread = 1.4826 * float(np.median(np.abs(scores - cmed))) + config.EPS
        p_high = float(np.percentile(scores, config.T_HIGH_PCTL))
        # T_high must clear both the MAD-based level and the at-rest percentile.
        self.t_high = max(cmed + config.K_HIGH * cspread, p_high * config.T_MARGIN)
        self.t_low = max(cmed + config.K_LOW * cspread, self.t_high * 0.6)
        self.state = "CLEAR"

    def _z(self, k: str, x: float) -> float:
        center, spread = self.baseline[k]
        return min(config.Z_CAP, abs(x - center) / (1.4826 * spread + config.EPS))

    def _score(self, fd: dict) -> float:
        num = den = 0.0
        for k in config.FUSION_FEATURES:
            w = config.FUSION_WEIGHTS.get(k, 1.0)
            z = self._z(k, fd[k])
            num += w * z * z
            den += w
        return math.sqrt(num / den) if den else 0.0

    def update(self, fd: dict) -> tuple[str, float, dict]:
        score = self._score(fd)
        parts = {k: self._z(k, fd[k]) for k in config.FUSION_FEATURES}  # before drift
        if self.state == "MOTION":
            if score < self.t_low:
                self._exit += 1
                if self._exit >= config.N_EXIT:
                    self.state, self._exit = "CLEAR", 0
            else:
                self._exit = 0
        else:  # CLEAR
            if score > self.t_high:
                self._enter += 1
                if self._enter >= config.N_ENTER:
                    self.state, self._enter = "MOTION", 0
            else:
                self._enter = 0
                self._drift(fd)
        return self.state, score, parts

    def _drift(self, fd: dict) -> None:
        a = config.DRIFT_ALPHA
        if a <= 0:
            return
        for k in config.FUSION_FEATURES:
            center, spread = self.baseline[k]
            center = (1 - a) * center + a * fd[k]
            spread = (1 - a) * spread + a * abs(fd[k] - center)
            self.baseline[k] = (center, spread)


def _demo(cal_n: int = 12, live_n: int = 8) -> None:
    """Calibrate, then print live score/state so you can see Stage 3 working."""
    from time import sleep

    import pinger
    import wifi_reader
    from features import FeatureExtractor

    gw = pinger.find_gateway()
    fx, det = FeatureExtractor(), Detector()
    print(f"Calibrating ({cal_n} samples) - hold still...")
    cal: list[dict] = []
    while len(cal) < cal_n:
        fx.push(wifi_reader.read_sample(), pinger.ping(gw))
        if fx.ready:
            cal.append(fx.features())
        sleep(config.SAMPLE_INTERVAL_SEC)
    det.calibrate(cal)
    print(f"Baseline ready. T_low={det.t_low:.2f}  T_high={det.t_high:.2f}\n")
    for _ in range(live_n):
        fx.push(wifi_reader.read_sample(), pinger.ping(gw))
        state, score, _ = det.update(fx.features())
        print(f"{state:7}  score {score:.2f}  (T_high {det.t_high:.2f})")
        sleep(config.SAMPLE_INTERVAL_SEC)


if __name__ == "__main__":
    _demo()
