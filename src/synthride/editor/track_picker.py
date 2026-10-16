# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Finding the cell of the track under the mouse."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from synthride.core.tile import Tile
from synthride.core.track import Track
from synthride.core.track_parser import TrackParser

if TYPE_CHECKING:
    from synthride.editor.track_grid import TrackGrid

Point = tuple[float, float, float]


class TrackPicker:
    """Finds the cell a ray from the camera points at, in world coordinates, where the track runs toward -z.

    The ray hits the top of the first tile it meets, trying the heights from the highest down; where it only meets
    gaps, it points at the cell at the brush height, so new tiles can be laid there.
    """

    @staticmethod
    def cell_at(x: float, z: float) -> tuple[int, int]:
        """Return the ``(column, row)`` over the world point ``(x, z)``."""
        return math.floor(x / Tile.WIDTH), math.floor(-z / Tile.LENGTH)

    @classmethod
    def pick(
        cls, grid: TrackGrid, origin: Point, direction: Point, height: int, *, clamp: bool = False
    ) -> tuple[int, int] | None:
        """Return the cell the ray from ``origin`` along ``direction`` points at, None when it misses the track.

        With ``clamp``, a ray beside the track points at the nearest cell instead, as a drag does.
        """
        ox, oy, oz = origin
        dx, dy, dz = direction
        if dy >= 0:
            return None
        for level in range(TrackParser.MAX_LEVEL, 0, -1):
            t = (level * Tile.HEIGHT_UNIT - oy) / dy
            if t <= 0:
                continue
            column, row = cls.cell_at(ox + dx * t, oz + dz * t)
            cell = grid.cell(column, row)
            if cell is not None and int(cell[1]) == level:
                return column, row
        t = (height * Tile.HEIGHT_UNIT - oy) / dy
        if t <= 0:
            return None
        column, row = cls.cell_at(ox + dx * t, oz + dz * t)
        if clamp:
            return min(Track.COLUMNS - 1, max(0, column)), max(0, row)
        if 0 <= column < Track.COLUMNS and row >= 0:
            return column, row
        return None
