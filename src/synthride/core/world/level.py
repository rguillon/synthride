# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""A playable level."""

from dataclasses import dataclass

from synthride.core.world.track import Track


@dataclass(frozen=True)
class Level:
    """A playable level: a track plus its physical and survival parameters."""

    name: str
    track: Track
    gravity: float = 18.0
    oxygen_seconds: float = 90.0
    fuel_capacity: float = 100.0
