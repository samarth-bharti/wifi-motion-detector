"""WiFi Motion Detector — calibrate a quiet baseline, then detect motion live.

Usage:  python src/main.py     (hold still during calibration, then walk around)
"""
from __future__ import annotations

import os
from time import sleep, time

from rich.console import Console
from rich.live import Live

import config
import pinger
import wifi_reader
from dashboard import Dashboard
from detector import Detector
from features import FeatureExtractor

try:
    import winsound
except ImportError:          # non-Windows: no beep
    winsound = None


def _beep() -> None:
    if config.BEEP and winsound:
        winsound.Beep(880, 150)


def _read(fx: FeatureExtractor, gw):
    sample = wifi_reader.read_sample()
    fx.push(sample, pinger.ping(gw))
    return sample


def _calibrate(fx, det, gw, console) -> None:
    n = max(5, int(config.CALIBRATION_SEC / config.SAMPLE_INTERVAL_SEC))
    console.print(f"[cyan]Calibrating ~{config.CALIBRATION_SEC}s - hold still...[/]")
    cal: list[dict] = []
    while len(cal) < n:
        _read(fx, gw)
        if fx.ready:
            cal.append(fx.features())
        sleep(config.SAMPLE_INTERVAL_SEC)
    det.calibrate(cal)
    console.print(f"[green]Baseline ready.[/] "
                  f"T_low={det.t_low:.2f}  T_high={det.t_high:.2f}\n")


def main() -> None:
    console = Console()
    gw = pinger.find_gateway()
    if not gw:
        console.print("[yellow]No router found - set PING_TARGET in config to enable "
                      "RTT/loss cues. Continuing on WiFi cues only.[/]")

    fx, det, dash = FeatureExtractor(), Detector(), Dashboard()
    _calibrate(fx, det, gw, console)

    prev = det.state
    max_ticks = int(os.environ.get("WMD_MAX_TICKS", "0"))  # 0 = run until Ctrl-C
    ticks = 0
    with Live(console=console, refresh_per_second=config.DASHBOARD_FPS) as live:
        while True:
            start = time()
            sample = _read(fx, gw)
            state, score, parts = det.update(fx.features())
            if state == "MOTION" and prev != "MOTION":
                _beep()
            prev = state
            live.update(dash.render(state, score, parts, det, sample))
            ticks += 1
            if max_ticks and ticks >= max_ticks:
                break
            sleep(max(0.0, config.SAMPLE_INTERVAL_SEC - (time() - start)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
