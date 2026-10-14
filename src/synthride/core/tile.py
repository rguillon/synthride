from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from synthride.core.bounding_box import BoundingBox
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3


@dataclass(frozen=True)
class Tile:
    """One solid block of the track, occupying a 1x1 cell and rising from the abyss to its top."""

    SIZE: ClassVar[float] = 1.0
    HEIGHT_UNIT: ClassVar[float] = 0.5
    BOTTOM: ClassVar[float] = -10.0

    tile_type: TileType
    column: int
    row: int
    level: int

    @property
    def top(self) -> float:
        return self.level * self.HEIGHT_UNIT

    @property
    def bounding_box(self) -> BoundingBox:
        return BoundingBox(
            Vector3(self.column * self.SIZE, self.BOTTOM, self.row * self.SIZE),
            Vector3((self.column + 1) * self.SIZE, self.top, (self.row + 1) * self.SIZE),
        )
