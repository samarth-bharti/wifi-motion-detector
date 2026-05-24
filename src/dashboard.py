"""Live terminal dashboard (rich) — the demoable face of the detector.

Shows a big CLEAR/MOTION banner, the live motion score vs its thresholds, a
sparkline of recent scores, and a per-feature breakdown so you can see which
cues are driving a detection.
"""
from __future__ import annotations

import sys
from collections import deque

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import config


def _supports_unicode() -> bool:
    """True if the output encoding can render block characters."""
    enc = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        "▁█".encode(enc)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


_UTF = _supports_unicode()
_BLOCKS = "▁▂▃▄▅▆▇█" if _UTF else " .:-=+*#"   # sparkline ramp (8 levels either way)
_BAR = "█" if _UTF else "#"                     # contribution-bar fill
_STYLES = {"MOTION": "bold white on red", "CLEAR": "bold white on green",
           "CALIBRATING": "bold black on yellow", "NO LINK": "bold black on yellow"}
_BORDER = {"MOTION": "red", "CLEAR": "green",
           "CALIBRATING": "yellow", "NO LINK": "yellow"}


def _sparkline(values, scale: float, width: int = 48) -> str:
    """Render recent scores as a sparkline, scaled so `scale` ~= full height."""
    vals = list(values)[-width:]
    if not vals:
        return ""
    top = len(_BLOCKS) - 1
    return "".join(_BLOCKS[min(top, max(0, int(v / scale * top)))] for v in vals)


class Dashboard:
    def __init__(self):
        self.scores: deque[float] = deque(maxlen=60)

    def render(self, state, score, parts, det, sample):
        self.scores.append(score)

        hdr = Text(justify="center")
        if sample and sample.connected:
            hdr.append(f"{sample.ssid or '?'}   ", style="cyan")
            hdr.append(f"RSSI {sample.rssi} dBm ({sample.signal_pct}%)   ", style="white")
            hdr.append(f"Rx {sample.rx_rate or 0:.0f} Mbps", style="white")
        else:
            hdr.append("link disconnected", style="yellow")

        banner = Text(f"\n   {state}   \n", style=_STYLES.get(state, ""),
                      justify="center")

        meter = Text(justify="center")
        meter.append(f"score {score:5.2f}", style="bold")
        meter.append(f"    T_high {det.t_high:.2f}   T_low {det.t_low:.2f}", style="dim")
        scale = max(det.t_high * 1.6, max(self.scores, default=0.0), 1e-6)
        spark = Text(_sparkline(self.scores, scale), style="magenta", justify="center")

        tbl = Table.grid(padding=(0, 1))
        tbl.add_column(justify="right", style="cyan")
        tbl.add_column()
        for k in config.FUSION_FEATURES:
            z = parts.get(k, 0.0)
            bar = _BAR * min(20, int(z * 3))
            tbl.add_row(k, Text(f"{bar} {z:.1f}", style="yellow"))

        body = Group(Align.center(hdr), Align.center(banner),
                     Align.center(meter), Align.center(spark),
                     Text(), Align.center(tbl))
        return Panel(body, title="WiFi Motion Detector",
                     subtitle="Ctrl-C to stop", border_style=_BORDER.get(state, "blue"))
