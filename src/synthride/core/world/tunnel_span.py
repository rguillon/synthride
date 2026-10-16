# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Tunnel spans: runs of tunnel tiles covered by a single shell."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import ClassVar

from synthride.core.physics.bounding_box import BoundingBox
from synthride.core.physics.solid import Solid
from synthride.core.physics.vector3 import Vector3
from synthride.core.world.tile import Tile
from synthride.core.world.tunnel_kind import TunnelKind

Point = tuple[float, float]


@dataclass(frozen=True)
class TunnelSpan:
    """A run of side-by-side tunnel tiles in one row, of one kind and height, covered by a single shell.

    The shell's cross-section is the area between its outer and inner paths. Both run from the left foot,
    over the top, to the right foot, as (x, y) points that pair up one to one, so the renderer can stitch
    them together. For collisions, the shell is cut into vertical slices: a round roof becomes a staircase
    whose ceiling never rises above the real arch.
    """

    WALL: ClassVar[float] = 0.1
    CLEARANCE: ClassVar[float] = 0.9  # inner height of a square tunnel
    ROOF: ClassVar[float] = 0.12
    SPRING: ClassVar[float] = 0.4  # height at which a round tunnel starts to curve
    MAX_RISE: ClassVar[float] = 0.9
    SHELL: ClassVar[float] = 0.12
    ARCH_SEGMENTS: ClassVar[int] = 18
    SLICE_WIDTH: ClassVar[float] = 0.2

    kind: TunnelKind
    row: int
    first_column: int
    last_column: int
    deck: float

    @property
    def left(self) -> float:
        """The x coordinate of the shell's left side."""
        return self.first_column * Tile.WIDTH

    @property
    def right(self) -> float:
        """The x coordinate of the shell's right side."""
        return (self.last_column + 1) * Tile.WIDTH

    @property
    def start(self) -> float:
        """The z coordinate of the shell's near end."""
        return self.row * Tile.LENGTH

    @property
    def end(self) -> float:
        """The z coordinate of the shell's far end."""
        return (self.row + 1) * Tile.LENGTH

    @property
    def center(self) -> float:
        """The x coordinate of the tunnel's centre."""
        return (self.left + self.right) / 2

    @property
    def half_width(self) -> float:
        """Half the outer width of the shell."""
        return (self.right - self.left) / 2

    @property
    def inner_half_width(self) -> float:
        """Half the width inside the walls."""
        return self.half_width - self.WALL

    @property
    def rise(self) -> float:
        """How high the round roof rises above its springing line."""
        return min(self.MAX_RISE, self.inner_half_width)

    def continues(self, other: TunnelSpan | None) -> bool:
        """Return True when ``other`` is the same tunnel one row further, so no mouth separates them."""
        return other is not None and (other.kind, other.first_column, other.last_column, other.deck) == (
            self.kind,
            self.first_column,
            self.last_column,
            self.deck,
        )

    def outer_path(self) -> list[Point]:
        """Return the shell's outer outline, from the left foot to the right foot."""
        if self.kind is TunnelKind.SQUARE:
            top = self.deck + self.CLEARANCE + self.ROOF
            return [(self.left, self.deck), (self.left, top), (self.right, top), (self.right, self.deck)]
        return [(self.left, self.deck), *self._arch(self.half_width, self.rise + self.SHELL), (self.right, self.deck)]

    def inner_path(self) -> list[Point]:
        """Return the shell's inner outline, from the left foot to the right foot."""
        left, right = self.left + self.WALL, self.right - self.WALL
        if self.kind is TunnelKind.SQUARE:
            top = self.deck + self.CLEARANCE
            return [(left, self.deck), (left, top), (right, top), (right, self.deck)]
        return [(left, self.deck), *self._arch(self.inner_half_width, self.rise), (right, self.deck)]

    def _arch(self, half_width: float, rise: float) -> list[Point]:
        base = self.deck + self.SPRING
        angles = (math.pi * (1 - step / self.ARCH_SEGMENTS) for step in range(self.ARCH_SEGMENTS + 1))
        return [(self.center + half_width * math.cos(angle), base + rise * math.sin(angle)) for angle in angles]

    def solids(self) -> list[Solid]:
        """Return the walls and roof slices the ship collides with."""
        wall_top = self.outer_height(self.left + self.WALL)
        parts = [
            (self.left, self.left + self.WALL, self.deck, wall_top),
            (self.right - self.WALL, self.right, self.deck, wall_top),
        ]
        if self.kind is TunnelKind.SQUARE:
            parts.append((self.left + self.WALL, self.right - self.WALL, self.deck + self.CLEARANCE, wall_top))
        else:
            parts.extend(self._roof_slices())
        return [Solid(BoundingBox(Vector3(x0, y0, self.start), Vector3(x1, y1, self.end))) for x0, x1, y0, y1 in parts]

    def _roof_slices(self) -> list[tuple[float, float, float, float]]:
        start, end = self.left + self.WALL, self.right - self.WALL
        count = math.ceil((end - start) / self.SLICE_WIDTH - 1e-9)
        width = (end - start) / count
        slices = []
        for index in range(count):
            x0, x1 = start + index * width, start + (index + 1) * width
            farthest = x0 if abs(x0 - self.center) > abs(x1 - self.center) else x1
            nearest = self.center if x0 <= self.center <= x1 else x1 if farthest == x0 else x0
            slices.append((x0, x1, self.inner_height(farthest), self.outer_height(nearest)))
        return slices

    def inner_height(self, x: float) -> float:
        """Return the height of the ceiling above ``x``."""
        if self.kind is TunnelKind.SQUARE:
            return self.deck + self.CLEARANCE
        return self.deck + self.SPRING + self.rise * self._dome(x, self.inner_half_width)

    def outer_height(self, x: float) -> float:
        """Return the height of the shell's outside above ``x``."""
        if self.kind is TunnelKind.SQUARE:
            return self.deck + self.CLEARANCE + self.ROOF
        return self.deck + self.SPRING + (self.rise + self.SHELL) * self._dome(x, self.half_width)

    def _dome(self, x: float, half_width: float) -> float:
        offset = (x - self.center) / half_width
        return math.sqrt(max(0.0, 1 - offset * offset))
