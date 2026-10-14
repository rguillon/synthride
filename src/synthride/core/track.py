from __future__ import annotations

import math
from collections.abc import Iterator, Sequence

from synthride.core.bounding_box import BoundingBox
from synthride.core.solid import Solid
from synthride.core.tile import Tile
from synthride.core.tunnel_kind import TunnelKind
from synthride.core.tunnel_span import TunnelSpan


class Track:
    """A grid of tiles, eight columns wide, laid out row after row along the z axis.

    Side-by-side tunnel tiles of one kind and height in a row merge into a single tunnel span.
    """

    COLUMNS = 8

    def __init__(self, rows: Sequence[Sequence[Tile | None]]) -> None:
        if any(len(row) != self.COLUMNS for row in rows):
            raise ValueError(f"every track row must have {self.COLUMNS} cells")  # noqa: TRY003
        self._rows = tuple(tuple(row) for row in rows)
        self._tunnels = tuple(span for row in self._rows for span in self._spans_in(row))
        self._tunnels_by_row: dict[int, list[TunnelSpan]] = {}
        for span in self._tunnels:
            self._tunnels_by_row.setdefault(span.row, []).append(span)
        self._solids: dict[tuple[int, int], list[Solid]] = {}
        for tile in self.tiles():
            self._solids.setdefault((tile.column, tile.row), []).append(Solid(tile.bounding_box, tile))
        for span in self._tunnels:
            for solid in span.solids():
                first, last = math.floor(solid.box.minimum.x / Tile.SIZE), math.ceil(solid.box.maximum.x / Tile.SIZE)
                for column in range(first, last):
                    self._solids.setdefault((column, span.row), []).append(solid)

    @staticmethod
    def _spans_in(row: Sequence[Tile | None]) -> Iterator[TunnelSpan]:
        run: list[tuple[TunnelKind, Tile]] = []
        for tile in (*row, None):
            if run and (tile is None or (tile.tunnel, tile.level) != (run[0][0], run[0][1].level)):
                kind, first = run[0]
                yield TunnelSpan(kind, first.row, first.column, run[-1][1].column, first.top)
                run = []
            if tile is not None and tile.tunnel is not None:
                run.append((tile.tunnel, tile))

    @property
    def row_count(self) -> int:
        return len(self._rows)

    @property
    def length(self) -> float:
        return self.row_count * Tile.SIZE

    @property
    def width(self) -> float:
        return self.COLUMNS * Tile.SIZE

    @property
    def tunnels(self) -> tuple[TunnelSpan, ...]:
        return self._tunnels

    def tile_at(self, column: int, row: int) -> Tile | None:
        if 0 <= column < self.COLUMNS and 0 <= row < self.row_count:
            return self._rows[row][column]
        return None

    def tiles(self) -> Iterator[Tile]:
        for row in self._rows:
            yield from (tile for tile in row if tile is not None)

    def tiles_under(self, box: BoundingBox) -> list[Tile]:
        """Tiles whose footprint overlaps the footprint of ``box``."""
        return [solid.tile for solid in self.solids_under(box) if solid.tile is not None]

    def solids_under(self, box: BoundingBox) -> list[Solid]:
        """Tile blocks and tunnel pieces whose footprint overlaps the footprint of ``box``."""
        first_column = math.floor(box.minimum.x / Tile.SIZE)
        last_column = math.ceil(box.maximum.x / Tile.SIZE)
        first_row = math.floor(box.minimum.z / Tile.SIZE)
        last_row = math.ceil(box.maximum.z / Tile.SIZE)
        found: dict[int, Solid] = {}
        for row in range(first_row, last_row):
            for column in range(first_column, last_column):
                for solid in self._solids.get((column, row), ()):
                    if id(solid) not in found and solid.box.overlaps_footprint(box):
                        found[id(solid)] = solid
        return list(found.values())

    def ceiling_over(self, x: float, first_z: float, last_z: float) -> float | None:
        """The lowest tunnel ceiling above ``x`` from ``first_z`` to ``last_z``, or None when no tunnel covers it."""
        first_row, last_row = math.floor(first_z / Tile.SIZE), math.floor(last_z / Tile.SIZE)
        ceilings = [
            span.inner_height(x)
            for row in range(first_row, last_row + 1)
            for span in self._tunnels_by_row.get(row, ())
            if span.left <= x < span.right
        ]
        return min(ceilings, default=None)

    def surface_height_at(self, x: float, z: float) -> float | None:
        tile = self.tile_at(math.floor(x / Tile.SIZE), math.floor(z / Tile.SIZE))
        return None if tile is None else tile.top
