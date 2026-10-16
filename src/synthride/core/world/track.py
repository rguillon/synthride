# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The track: a grid of tiles and the tunnels on them."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from synthride.core.physics.solid import Solid
from synthride.core.world.tile import Tile
from synthride.core.world.tunnel_span import TunnelSpan

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from synthride.core.physics.bounding_box import BoundingBox
    from synthride.core.world.tunnel_kind import TunnelKind


class Track:
    """A grid of tiles, eight columns wide, laid out row after row along the z axis.

    Side-by-side tunnel tiles of one kind and height in a row merge into a single tunnel span.
    """

    COLUMNS = 8

    def __init__(self, rows: Sequence[Sequence[Tile | None]]) -> None:
        """Build a track from ``rows`` of eight cells each, None meaning a gap."""
        if any(len(row) != self.COLUMNS for row in rows):
            msg = f"every track row must have {self.COLUMNS} cells"
            raise ValueError(msg)
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
                first, last = math.floor(solid.box.minimum.x / Tile.WIDTH), math.ceil(solid.box.maximum.x / Tile.WIDTH)
                for column in range(first, last):
                    self._solids.setdefault((column, span.row), []).append(solid)
        # Each cell's solids with their footprints, as looked up by solids_under for every step of the ship.
        self._footprints = {
            cell: tuple(
                (solid, solid.box.minimum.x, solid.box.maximum.x, solid.box.minimum.z, solid.box.maximum.z)
                for solid in solids
            )
            for cell, solids in self._solids.items()
        }

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
        """The number of rows."""
        return len(self._rows)

    @property
    def length(self) -> float:
        """The length of the track along the z axis."""
        return self.row_count * Tile.LENGTH

    @property
    def width(self) -> float:
        """The width of the track along the x axis."""
        return self.COLUMNS * Tile.WIDTH

    @property
    def tunnels(self) -> tuple[TunnelSpan, ...]:
        """Every tunnel span, row by row."""
        return self._tunnels

    def tile_at(self, column: int, row: int) -> Tile | None:
        """Return the tile in a cell, or None for a gap or a cell outside the track."""
        if 0 <= column < self.COLUMNS and 0 <= row < self.row_count:
            return self._rows[row][column]
        return None

    def tiles(self) -> Iterator[Tile]:
        """Yield every tile, row by row."""
        for row in self._rows:
            yield from (tile for tile in row if tile is not None)

    def tiles_under(self, box: BoundingBox) -> list[Tile]:
        """Tiles whose footprint overlaps the footprint of ``box``."""
        return [solid.tile for solid in self.solids_under(box) if solid.tile is not None]

    def solids_under(self, box: BoundingBox) -> list[Solid]:
        """Tile blocks and tunnel pieces whose footprint overlaps the footprint of ``box``."""
        first_column = math.floor(box.minimum.x / Tile.WIDTH)
        last_column = math.ceil(box.maximum.x / Tile.WIDTH)
        first_row = math.floor(box.minimum.z / Tile.LENGTH)
        last_row = math.ceil(box.maximum.z / Tile.LENGTH)
        low_x, high_x, low_z, high_z = box.minimum.x, box.maximum.x, box.minimum.z, box.maximum.z
        found: list[Solid] = []
        seen: set[int] = set()
        for row in range(first_row, last_row):
            for column in range(first_column, last_column):
                for solid, solid_low_x, solid_high_x, solid_low_z, solid_high_z in self._footprints.get(
                    (column, row), ()
                ):
                    # The test of BoundingBox.overlaps_footprint, on footprints read once.
                    if not (
                        low_x < solid_high_x > solid_low_x < high_x > low_x
                        and low_z < solid_high_z > solid_low_z < high_z > low_z
                    ):
                        continue
                    if id(solid) not in seen:
                        seen.add(id(solid))
                        found.append(solid)
        return found

    def ceiling_over(self, x: float, first_z: float, last_z: float) -> float | None:
        """Return the lowest tunnel ceiling above ``x`` from ``first_z`` to ``last_z``, or None outside tunnels."""
        first_row, last_row = math.floor(first_z / Tile.LENGTH), math.floor(last_z / Tile.LENGTH)
        ceilings = [
            span.inner_height(x)
            for row in range(first_row, last_row + 1)
            for span in self._tunnels_by_row.get(row, ())
            if span.left <= x < span.right
        ]
        return min(ceilings, default=None)

    def surface_height_at(self, x: float, z: float) -> float | None:
        """Return the height of the tile's top face at ``(x, z)``, or None over a gap."""
        tile = self.tile_at(math.floor(x / Tile.WIDTH), math.floor(z / Tile.LENGTH))
        return None if tile is None else tile.height_at(x, z)
