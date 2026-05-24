"""Tests for the dashboard's motion-level mapping (pure function, no UI)."""
from dashboard import motion_level


def test_zero_score_is_zero():
    assert motion_level(0.0, 3.2) == 0


def test_threshold_lands_near_70pct():
    assert motion_level(3.2, 3.2) == 70


def test_high_score_caps_at_100():
    assert motion_level(10.0, 3.2) == 100


def test_guards_zero_threshold():
    assert motion_level(5.0, 0.0) == 0
