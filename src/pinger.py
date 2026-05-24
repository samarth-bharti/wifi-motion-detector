"""Ping the router for round-trip time (RTT) and packet loss — a second sense.

Motion in the room causes WiFi retransmissions, which show up as RTT spikes and
lost packets. Pinging the default gateway (your router) once per tick gives us
that signal, and keeps the WiFi link "warm" so the other readings stay fresh.
"""
from __future__ import annotations

import re
import subprocess

import config

# Matches the "=3ms" / "<1ms" time field in ping output (locale-tolerant).
_RTT = re.compile(r"[=<]\s*(\d+)\s*ms", re.IGNORECASE)


def _parse_rtt(text: str) -> float | None:
    """Pull RTT (ms) from `ping` output, or None if the packet was lost."""
    if "ttl=" not in text.lower():   # no TTL line => no reply => lost
        return None
    m = _RTT.search(text)
    return float(m.group(1)) if m else None


def find_gateway() -> str | None:
    """Return the default-gateway IP (the router), or the configured override."""
    if config.PING_TARGET:
        return config.PING_TARGET
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
             "Sort-Object RouteMetric | Select-Object -First 1).NextHop"],
            capture_output=True, text=True, timeout=8,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def ping(host: str | None, timeout_ms: int | None = None) -> float | None:
    """Ping `host` once. Returns RTT in ms, or None on loss/error."""
    if not host:
        return None
    timeout_ms = timeout_ms or config.PING_TIMEOUT_MS
    try:
        out = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), host],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            timeout=timeout_ms / 1000 + 2,
        ).stdout
    except Exception:
        return None
    return _parse_rtt(out)
