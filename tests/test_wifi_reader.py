"""Tests for the netsh parser — pure text parsing, no hardware needed."""
import wifi_reader

REAL = """
There is 1 interface on the system:

    Name                   : Wi-Fi
    State                  : connected
    SSID                   : BHARTI_HOME
    AP BSSID               : 70:b6:4f:7e:02:ef
    Band                   : 2.4 GHz
    Receive rate (Mbps)    : 162
    Transmit rate (Mbps)   : 52
    Signal                 : 54%
    Rssi                   : -71
    Profile                : BHARTI_HOME
"""

NO_RSSI = """
    State                  : connected
    SSID                   : BHARTI_HOME
    Signal                 : 54%
"""

DISCONNECTED = """
    State                  : disconnected
"""


def test_parses_real_output():
    s = wifi_reader.parse_netsh(REAL)
    assert s.connected
    assert s.ssid == "BHARTI_HOME"
    assert s.bssid == "70:b6:4f:7e:02:ef"
    assert s.rssi == -71
    assert s.signal_pct == 54
    assert s.rx_rate == 162.0
    assert s.tx_rate == 52.0


def test_derives_rssi_from_signal_when_missing():
    s = wifi_reader.parse_netsh(NO_RSSI)
    assert s.rssi == 54 // 2 - 100  # -73
    assert s.signal_pct == 54


def test_handles_disconnected():
    s = wifi_reader.parse_netsh(DISCONNECTED)
    assert not s.connected
    assert s.rssi is None
