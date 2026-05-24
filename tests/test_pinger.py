"""Tests for ping-output parsing — pure text, no network needed."""
import pinger

REPLY = "Reply from 192.168.1.1: bytes=32 time=3ms TTL=64"
REPLY_SUBMS = "Reply from 192.168.1.1: bytes=32 time<1ms TTL=64"
TIMEOUT = "Request timed out."
UNREACHABLE = "Reply from 192.168.1.5: Destination host unreachable."


def test_parses_rtt():
    assert pinger._parse_rtt(REPLY) == 3.0


def test_parses_sub_millisecond():
    assert pinger._parse_rtt(REPLY_SUBMS) == 1.0


def test_timeout_is_loss():
    assert pinger._parse_rtt(TIMEOUT) is None


def test_unreachable_is_loss():
    assert pinger._parse_rtt(UNREACHABLE) is None
