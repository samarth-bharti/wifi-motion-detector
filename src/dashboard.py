"""Live terminal dashboard (rich) — the demoable face of the detector.

Top: plain-language status + a 0-100% motion meter (threshold marked).
Below: the technical details (per-cue z-scores, thresholds, score sparkline).
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
_BAR = "█" if _UTF else "#"                     # bar fill
_STYLES = {"MOTION": "bold white on red", "CLEAR": "bold white on green",
           "CALIBRATING": "bold black on yellow", "NO LINK": "bold black on yellow"}
_BORDER = {"MOTION": "red", "CLEAR": "green",
           "CALIBRATING": "yellow", "NO LINK": "yellow"}
_WORDS = {"MOTION": "MOVEMENT DETECTED", "CLEAR": "ROOM QUIET",
          "CALIBRATING": "CALIBRATING...", "NO LINK": "WIFI DISCONNECTED"}
_HINT = {"MOTION": "Movement is disturbing the WiFi signal.",
         "CLEAR": "Quiet. Walk across the laptop->router path to test.",
         "CALIBRATING": "Learning the quiet baseline - hold still.",
         "NO LINK": "WiFi link lost - detection paused."}
_TRIP = 0.70   # where T_high sits on the 0-100% meter


def motion_level(score: float, t_high: float) -> int:
    """Map score to 0-100%, with the trip threshold landing at ~70%."""
    if t_high <= 0:
        return 0
    return int(min(100, max(0, score / t_high * (_TRIP * 100))))


def _sparkline(values, scale: float, width: int = 48) -> str:
    vals = list(values)[-width:]
    if not vals:
        return ""
    top = len(_BLOCKS) - 1
    return "".join(_BLOCKS[min(top, max(0, int(v / scale * top)))] for v in vals)


def _meter(level: int, motion: bool, width: int = 28) -> Text:
    """A colored 0-100% bar with a '|' marker at the trip threshold."""
    fill = int(round(level / 100 * width))
    mark = int(round(_TRIP * width))
    t = Text("  [")
    for i in range(width):
        if i == mark:
            t.append("|", style="bold white")
        elif i < fill:
            t.append(_BAR, style="red" if motion else "green")
        else:
            t.append("-", style="dim")
    t.append(f"] {level:3d}%", style="bold")
    return t


class Dashboard:
    def __init__(self):
        self.scores: deque[float] = deque(maxlen=60)

    def render(self, state, score, parts, det, sample):
        self.scores.append(score)
        motion = state == "MOTION"

        hdr = Text(justify="center")
        if sample and sample.connected:
            hdr.append(f"{sample.ssid or '?'}   ", style="cyan")
            hdr.append(f"RSSI {sample.rssi} dBm ({sample.signal_pct}%)   ", style="white")
            hdr.append(f"Rx {sample.rx_rate or 0:.0f} Mbps", style="white")
        else:
            hdr.append("link disconnected", style="yellow")

        banner = Text(f"\n  {_WORDS.get(state, state)}  \n",
                      style=_STYLES.get(state, ""), justify="center")
        meter = Align.center(_meter(motion_level(score, det.t_high), motion))
        hint = Text(_HINT.get(state, ""), style="italic", justify="center")

        det_hdr = Text("- details -", style="dim", justify="center")
        nums = Text(f"score {score:5.2f}    T_high {det.t_high:.2f}   T_low {det.t_low:.2f}",
                    style="dim", justify="center")
        scale = max(det.t_high * 1.6, max(self.scores, default=0.0), 1e-6)
        spark = Text(_sparkline(self.scores, scale), style="magenta", justify="center")
        tbl = Table.grid(padding=(0, 1))
        tbl.add_column(justify="right", style="cyan")
        tbl.add_column()
        for k in config.FUSION_FEATURES:
            z = parts.get(k, 0.0)
            tbl.add_row(k, Text(f"{_BAR * min(20, int(z * 3))} {z:.1f}", style="yellow"))

        body = Group(
            Align.center(hdr), Align.center(banner), meter, Align.center(hint),
            Text(), Align.center(det_hdr), Align.center(nums), Align.center(spark),
            Text(), Align.center(tbl),
        )
        return Panel(body, title="WiFi Motion Detector",
                     subtitle="keep the laptop still (it is the sensor)  |  Ctrl-C to quit",
                     border_style=_BORDER.get(state, "blue"))
