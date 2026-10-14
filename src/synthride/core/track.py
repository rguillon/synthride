from __future__ import annotations

import math
from collections.abc import Iterator, Sequence

from synthride.core.bounding_box import BoundingBox
from synthride.core.tile import Tile


class Track:
    """A grid of tiles, eight columns wide, laid out row after row along the z axis."""

    COLUMNS = 8

    def __init__(self, rows: Sequence[Sequence[Tile | None]]) -> None:
        if any(len(row) != self.COLUMNS for row in rows):
            raise ValueError(f"every track row must have {self.COLUMNS} cells")  # noqa: TRY003
        self._rows = tuple(tuple(row) for row in rows)

    @property
    def row_count(self) -> int:
        return len(self._rows)

    @property
    def length(self) -> float:
        return self.row_count * Tile.SIZE

    @property
    def width(self) -> float:
        return self.COLUMNS * Tile.SIZE

    def tile_at(self, column: int, row: int) -> Tile | None:
        if 0 <= column < self.COLUMNS and 0 <= row < self.row_count:
            return self._rows[row][column]
        return None

    def tiles(self) -> Iterator[Tile]:
        for row in self._rows:
            yield from (tile for tile in row if tile is not None)

    def tiles_under(self, box: BoundingBox) -> list[Tile]:
        """Tiles whose footprint overlaps the footprint of ``box``."""
        first_column = math.floor(box.minimum.x / Tile.SIZE)
        last_column = math.ceil(box.maximum.x / Tile.SIZE)
        first_row = math.floor(box.minimum.z / Tile.SIZE)
        last_row = math.ceil(box.maximum.z / Tile.SIZE)
        found = []
        for row in range(first_row, last_row):
            for column in range(first_column, last_column):
                tile = self.tile_at(column, row)
                if tile is not None and tile.bounding_box.overlaps_footprint(box):
                    found.append(tile)
        return found

    def surface_height_at(self, x: float, z: float) -> float | None:
        tile = self.tile_at(math.floor(x / Tile.SIZE), math.floor(z / Tile.SIZE))
        return None if tile is None else tile.top
