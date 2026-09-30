"""
Jarvis Space Monitor.

R8.7:
    authoritative remote space-weather observations

Future:
    R8.8 near-Earth objects
    R8.9 orbital objects
    local RF/GPS observations
"""

from .service import build_space_weather_snapshot

__all__ = ["build_space_weather_snapshot"]
