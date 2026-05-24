"""Sliding-window feature extraction — turn raw readings into motion cues.

We keep the last WINDOW readings and summarise them into a feature vector:
- 'level' features are the latest value (signal %, rssi, rx rate, rtt);
- 'wobble' features are the rolling std (how much a value is bouncing around) —
  motion makes the wobble grow;
- 'loss' is the fraction of pings lost in the window.
The detector (Stage 3) decides which of these actually matter for your room.
"""
from __future__ import annotations

from collections import deque

import numpy as np

import config


def _last(d) -> float:
    return float(d[-1]) if d else 0.0


def _std(d) -> float:
    return float(np.std(d)) if len(d) >= 2 else 0.0


class FeatureExtractor:
    def __init__(self, window: int = config.WINDOW):
        self.window = window
        self._rssi = deque(maxlen=window)
        self._signal = deque(maxlen=window)
        self._rx = deque(maxlen=window)
        self._rtt = deque(maxlen=window)   # None entries = lost pings

    def push(self, sample, rtt) -> None:
        if sample.rssi is not None:
            self._rssi.append(sample.rssi)
        if sample.signal_pct is not None:
            self._signal.append(sample.signal_pct)
        if sample.rx_rate is not None:
            self._rx.append(sample.rx_rate)
        self._rtt.append(rtt)

    @property
    def ready(self) -> bool:
        """True once we have enough history for meaningful rolling stats."""
        return len(self._signal) >= max(3, self.window // 2)

    def features(self) -> dict[str, float]:
        rtt_vals = [r for r in self._rtt if r is not None]
        lost = sum(1 for r in self._rtt if r is None)
        total = len(self._rtt) or 1
        return {
            "signal": _last(self._signal),
            "signal_std": _std(self._signal),
            "rssi": _last(self._rssi),
            "rssi_std": _std(self._rssi),
            "rx_rate": _last(self._rx),
            "rtt": float(np.median(rtt_vals)) if rtt_vals else 0.0,
            "rtt_std": float(np.std(rtt_vals)) if len(rtt_vals) >= 2 else 0.0,
            "loss": lost / total,
        }


def _demo(n: int = 12) -> None:
    """Print a live feature vector each tick so you can see Stage 2 working."""
    from time import sleep

    import pinger
    import wifi_reader

    gw = pinger.find_gateway()
    print(f"router (gateway): {gw}\n")
    fx = FeatureExtractor()
    for _ in range(n):
        sample = wifi_reader.read_sample()
        rtt = pinger.ping(gw)
        fx.push(sample, rtt)
        if fx.ready:
            f = fx.features()
            print(f"signal {f['signal']:.0f}% (sd {f['signal_std']:.1f})  "
                  f"rssi {f['rssi']:.0f} (sd {f['rssi_std']:.1f})  "
                  f"rx {f['rx_rate']:.0f}  "
                  f"rtt {f['rtt']:.0f}ms (sd {f['rtt_std']:.1f})  "
                  f"loss {f['loss'] * 100:.0f}%")
        else:
            print("warming up window...")
        sleep(config.SAMPLE_INTERVAL_SEC)


if __name__ == "__main__":
    _demo()
