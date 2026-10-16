# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""How far and how high the ship can surely get, from the physics tunables."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from synthride.core.game_config import GameConfig
from synthride.core.tile import Tile


@dataclass(frozen=True)
class TrackReach:
    """Conservative limits of what the ship can do on a level of gravity ``gravity``.

    Jumps are judged with the double jump pressed at the top of the first jump, and only ``margin`` of the distance
    and of the height the physics allow is counted, so that a level built within these limits leaves room for
    imperfect piloting.
    """

    config: GameConfig = field(default_factory=GameConfig)
    gravity: float = 18.0
    margin: float = 0.65

    @property
    def slow_speed(self) -> float:
        """The speed a slow tile caps the ship to."""
        return self.config.max_speed * self.config.slow_factor

    def apex(self, launch: float) -> float:
        """Return how high above its take-off a jump launched upward at ``launch`` rises, double jump included."""
        return (launch * launch + self.config.double_jump_velocity**2) / (2 * self.gravity)

    def flight_time(self, launch: float, rise: float) -> float | None:
        """Return how long a jump launched at ``launch`` takes to come down to ``rise`` above its take-off.

        Return None when the jump does not surely rise that high.
        """
        if rise > self.margin * self.apex(launch):
            return None
        second = self.config.double_jump_velocity
        top = launch * launch / (2 * self.gravity)
        return (launch + second + math.sqrt(second * second + 2 * self.gravity * (top - rise))) / self.gravity

    def can_jump(self, launch: float, speed: float, gap_rows: int, rise: float, extra: float = 0.0) -> bool:
        """Return True if a jump at ``speed`` surely clears ``gap_rows`` empty rows to land ``rise`` higher.

        The ship takes off ``extra`` before the very end of its row and must land with its whole length on the
        landing row.
        """
        time = self.flight_time(launch, rise)
        if time is None:
            return False
        return gap_rows * Tile.LENGTH + self.config.ship_length + extra <= self.margin * speed * time

    def max_gap(self, launch: float, speed: float, rise: float) -> int:
        """Return the most empty rows a jump at ``speed`` surely clears to land ``rise`` higher, -1 if none."""
        time = self.flight_time(launch, rise)
        if time is None:
            return -1
        return math.floor((self.margin * speed * time - self.config.ship_length) / Tile.LENGTH)

    def max_rise_levels(self, launch: float) -> int:
        """Return how many height levels a jump launched at ``launch`` surely climbs."""
        return math.floor(self.margin * self.apex(launch) / Tile.HEIGHT_UNIT + 1e-9)

    def next_speed(self, speed: float, cap: float) -> float:
        """Return the most speed the ship can have one row after having ``speed``, never above ``cap``."""
        return min(cap, math.sqrt(speed * speed + 2 * self.config.acceleration * Tile.LENGTH))
