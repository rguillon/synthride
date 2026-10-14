# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Track tiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from synthride.core.bounding_box import BoundingBox
from synthride.core.vector3 import Vector3

if TYPE_CHECKING:
    from synthride.core.slope import Slope
    from synthride.core.tile_type import TileType
    from synthride.core.tunnel_kind import TunnelKind


@dataclass(frozen=True)
class Tile:
    """One solid block of the track, occupying a 1x1 cell and rising from the abyss to its top.

    A tile may carry a tunnel, whose shell stands on its top. An oblique tile has a ``slope``: its top
    rises from ``level`` on its low side to one height unit more on its raised side or corner.
    """

    SIZE: ClassVar[float] = 1.0
    HEIGHT_UNIT: ClassVar[float] = 0.5
    BOTTOM: ClassVar[float] = -10.0

    tile_type: TileType
    column: int
    row: int
    level: int
    tunnel: TunnelKind | None = None
    slope: Slope | None = None

    @property
    def base(self) -> float:
        """The height of the lowest point of the tile's top face."""
        return self.level * self.HEIGHT_UNIT

    @property
    def top(self) -> float:
        """The height of the highest point of the tile's top face."""
        return self.base + (self.HEIGHT_UNIT if self.slope is not None else 0.0)

    def height_at(self, x: float, z: float) -> float:
        """Return the height of the top face above ``(x, z)``, clamped to the tile."""
        if self.slope is None:
            return self.base
        return self.base + self.HEIGHT_UNIT * self.slope.rise(*self._local(x, z))

    def gradient(self, x: float, z: float) -> tuple[float, float]:
        """Return how steeply the top face rises at ``(x, z)``, clamped to the tile, as height per unit along x, z."""
        if self.slope is None:
            return 0.0, 0.0
        steepness = self.HEIGHT_UNIT / self.SIZE
        x_sign, z_sign = self.slope.gradient(*self._local(x, z))
        return x_sign * steepness, z_sign * steepness

    def _local(self, x: float, z: float) -> tuple[float, float]:
        """Return ``(x, z)`` relative to the tile, from 0 to 1 along each axis, clamped to the tile."""
        return min(1.0, max(0.0, x / self.SIZE - self.column)), min(1.0, max(0.0, z / self.SIZE - self.row))

    def corner_height(self, corner_x: int, corner_z: int) -> float:
        """Return the height of the top face at one of its corners, given as 0 or 1 along each axis."""
        return self.height_at((self.column + corner_x) * self.SIZE, (self.row + corner_z) * self.SIZE)

    def top_over(self, box: BoundingBox) -> float:
        """Return the highest point of the top face over the part of the tile covered by the footprint of ``box``.

        Every slope rises monotonically along each axis, so the highest point is one of the corners of that part.
        """
        if self.slope is None:
            return self.base
        return max(self.height_at(x, z) for x in (box.minimum.x, box.maximum.x) for z in (box.minimum.z, box.maximum.z))

    @property
    def bounding_box(self) -> BoundingBox:
        """The tile's solid block, from the abyss to its top."""
        return BoundingBox(
            Vector3(self.column * self.SIZE, self.BOTTOM, self.row * self.SIZE),
            Vector3((self.column + 1) * self.SIZE, self.top, (self.row + 1) * self.SIZE),
        )
