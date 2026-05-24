"""Tests for the fusion detector — synthetic feature streams, no hardware."""
from detector import Detector


def feat(signal=48, signal_std=3.0, rssi_std=0.0, rx=140.0,
         rtt=6.0, rtt_std=1.4, loss=0.0):
    return {"signal": signal, "signal_std": signal_std, "rssi": -71,
            "rssi_std": rssi_std, "rx_rate": rx, "rtt": rtt,
            "rtt_std": rtt_std, "loss": loss}


def quiet_calibration():
    """20 mildly-varying 'still room' samples (nonzero spread for robust stats)."""
    cal = []
    for i in range(20):
        cal.append(feat(signal=48 + (i % 3 - 1) * 2,        # 46/48/50
                        signal_std=3.0 + (i % 2) * 0.5,
                        rtt_std=1.4 + (i % 2) * 0.2,
                        rx=140 + (i % 3 - 1) * 10))
    return cal


def calibrated_detector():
    det = Detector()
    det.calibrate(quiet_calibration())
    return det


def test_calibration_sets_sensible_thresholds():
    det = calibrated_detector()
    assert det.state == "CLEAR"
    assert det.t_low < det.t_high


def test_stays_clear_when_still():
    det = calibrated_detector()
    for _ in range(6):
        state, _, _ = det.update(feat())
    assert state == "CLEAR"


def test_flips_to_motion_on_disturbance():
    det = calibrated_detector()
    motion = feat(signal=30, signal_std=12, rtt=20, rtt_std=8, loss=0.4)
    for _ in range(4):
        state, score, _ = det.update(motion)
    assert state == "MOTION"
    assert score > det.t_high


def test_returns_to_clear_after_motion():
    det = calibrated_detector()
    motion = feat(signal=30, signal_std=12, rtt=20, rtt_std=8, loss=0.4)
    for _ in range(4):
        det.update(motion)
    assert det.state == "MOTION"
    for _ in range(5):
        det.update(feat())
    assert det.state == "CLEAR"


def test_single_spike_does_not_trip_motion():
    """Debounce: one noisy sample must not flip the state."""
    det = calibrated_detector()
    det.update(feat(signal=30, signal_std=12, rtt_std=8, loss=0.4))  # 1 spike
    det.update(feat())                                                # back to quiet
    assert det.state == "CLEAR"
