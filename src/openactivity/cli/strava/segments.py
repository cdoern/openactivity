"""Strava-specific segments commands — thin alias over top-level segments.

All commands delegate to the unified ``openactivity segments`` / ``openactivity segment``
commands.
"""

from __future__ import annotations

from openactivity.cli.segments import (
    segment_app,
    segments_app as app,
    show_segment_efforts,
    show_segment_leaderboard,
    show_segment_trend,
)

__all__ = [
    "app",
    "segment_app",
    "show_segment_efforts",
    "show_segment_leaderboard",
    "show_segment_trend",
]
