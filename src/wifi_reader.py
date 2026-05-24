"""Read and parse the laptop's live WiFi link stats from `netsh` — zero hardware.

Windows already measures signal strength and link rates to the router. We shell
out to `netsh wlan show interfaces`, parse the `key : value` lines, and return a
tidy WifiSample. RSSI (dBm) is primary; if it's missing we derive it from
Signal % (Windows uses signal% = 2*(rssi+100), so rssi = signal/2 - 100).
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from time import time

import config


@dataclass
class WifiSample:
    timestamp: float
    state: str | None
    ssid: str | None
    bssid: str | None
    rssi: int | None        # dBm, e.g. -71 (closer to 0 = stronger)
    signal_pct: int | None  # 0-100
    rx_rate: float | None   # Mbps (adaptive receive rate)
    tx_rate: float | None   # Mbps (adaptive transmit rate)

    @property
    def connected(self) -> bool:
        return (self.state or "").lower() == "connected"


def _to_int(s):
    try:
        return int(s.strip().rstrip("%").split()[0])
    except (ValueError, IndexError, AttributeError):
        return None


def _to_float(s):
    try:
        return float(s.strip().split()[0])
    except (ValueError, IndexError, AttributeError):
        return None


def parse_netsh(text: str) -> WifiSample:
    """Parse `netsh wlan show interfaces` output into a WifiSample.

    Splits each line on the first ':' so values containing colons (BSSID,
    MAC addresses) survive intact.
    """
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().lower()] = value.strip()

    rssi = _to_int(fields.get("rssi"))
    signal_pct = _to_int(fields.get("signal"))
    if rssi is None and signal_pct is not None:
        rssi = signal_pct // 2 - 100  # derive dBm from Signal %

    return WifiSample(
        timestamp=time(),
        state=fields.get("state"),
        ssid=fields.get("ssid") or None,
        bssid=fields.get("ap bssid") or None,
        rssi=rssi,
        signal_pct=signal_pct,
        rx_rate=_to_float(fields.get("receive rate (mbps)")),
        tx_rate=_to_float(fields.get("transmit rate (mbps)")),
    )


def read_sample() -> WifiSample:
    """Run netsh once and return the parsed sample. Raises on netsh failure."""
    result = subprocess.run(
        ["netsh", "wlan", "show", "interfaces"],
        capture_output=True, text=True, encoding="utf-8", errors="ignore",
        timeout=config.NETSH_TIMEOUT_SEC,
    )
    return parse_netsh(result.stdout)


def _demo(n: int = 10) -> None:
    """Print a few live readings so you can see Stage 1 working."""
    from time import sleep
    print("Reading live WiFi link (Ctrl-C to stop)...\n")
    for _ in range(n):
        s = read_sample()
        if s.connected:
            print(f"{s.ssid:<14} RSSI {s.rssi} dBm ({s.signal_pct}%)  "
                  f"Rx {s.rx_rate} / Tx {s.tx_rate} Mbps")
        else:
            print(f"[not connected] state={s.state}")
        sleep(config.SAMPLE_INTERVAL_SEC)


if __name__ == "__main__":
    _demo()
