"""Compatibility API; startup owns canonical platform detection."""
from core.bootstrap.discovery.platform import detect_platform


def detect_environment():
    return detect_platform()
