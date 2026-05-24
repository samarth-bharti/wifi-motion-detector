"""Tests for sliding-window feature extraction — synthetic samples, no hardware."""
from features import FeatureExtractor
from wifi_reader import WifiSample


def _sample(signal, rssi=-70, rx=100.0):
    return WifiSample(timestamp=0.0, state="connected", ssid="X", bssid=None,
                      rssi=rssi, signal_pct=signal, rx_rate=rx, tx_rate=rx)


def test_flat_signal_has_zero_wobble():
    fx = FeatureExtractor(window=8)
    for _ in range(8):
        fx.push(_sample(50), rtt=5.0)
    f = fx.features()
    assert f["signal"] == 50
    assert f["signal_std"] == 0.0
    assert f["loss"] == 0.0


def test_varying_signal_has_wobble():
    fx = FeatureExtractor(window=8)
    for v in (40, 60, 40, 60, 40, 60, 40, 60):
        fx.push(_sample(v), rtt=5.0)
    f = fx.features()
    assert f["signal_std"] > 5.0


def test_loss_fraction_counts_dropped_pings():
    fx = FeatureExtractor(window=4)
    for rtt in (5.0, None, 5.0, None):
        fx.push(_sample(50), rtt=rtt)
    assert fx.features()["loss"] == 0.5


def test_ready_requires_minimum_history():
    fx = FeatureExtractor(window=8)
    fx.push(_sample(50), rtt=5.0)
    assert not fx.ready
    for _ in range(4):
        fx.push(_sample(50), rtt=5.0)
    assert fx.ready
