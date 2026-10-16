# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Builds levels for tests."""

from synthride.core.world.level import Level
from synthride.core.world.track_parser import TrackParser


def make_level(*rows: str, name: str = "Untitled", **settings: float) -> Level:
    """Return a level with the given settings (``oxygen_seconds``...) and track rows, each used once."""
    track = TrackParser().parse([(1, line) for row in rows for line in row.splitlines()])
    return Level(name=name, track=track, **settings)
