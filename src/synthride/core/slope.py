# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The shapes of oblique tiles."""

from __future__ import annotations

from enum import Enum


class Slope(Enum):
    """Which side or corner of an oblique tile is raised. The value is the suffix used in level files.

    Front is the far end of the tile (toward +z, where the track goes), right is +x. A side slope is a ramp
    rising toward that side; a corner slope rises toward that one corner only, so it joins two side ramps
    around the corner of a raised plateau.
    """

    FRONT = "f"
    BACK = "b"
    LEFT = "l"
    RIGHT = "r"
    FRONT_LEFT = "fl"
    FRONT_RIGHT = "fr"
    BACK_LEFT = "bl"
    BACK_RIGHT = "br"

    @property
    def direction(self) -> tuple[int, int]:
        """The raised side as (x, z) signs: -1, 0 or 1 on each axis."""
        x = 1 if "r" in self.value else -1 if "l" in self.value else 0
        z = 1 if "f" in self.value else -1 if "b" in self.value else 0
        return x, z

    def rise(self, u: float, v: float) -> float:
        """Return how far up the slope the point ``(u, v)`` of the unit cell is, from 0 (low) to 1 (raised)."""
        return min(self._ramp(sign, t) for sign, t in zip(self.direction, (u, v), strict=True) if sign)

    def gradient(self, u: float, v: float) -> tuple[int, int]:
        """Return which way the slope rises at ``(u, v)``, as (x, z) signs. A corner rises along one axis at a time."""
        x, z = self.direction
        if x and z:
            return (x, 0) if self._ramp(x, u) <= self._ramp(z, v) else (0, z)
        return x, z

    @staticmethod
    def _ramp(sign: int, t: float) -> float:
        return t if sign > 0 else 1 - t
