# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Parsing of the run-length encoded track rows that levels are written in."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.core.world.slope import Slope
from synthride.core.world.tile import Tile
from synthride.core.world.tile_type import TileType
from synthride.core.world.track import Track
from synthride.core.world.tunnel_kind import TunnelKind

if TYPE_CHECKING:
    from collections.abc import Sequence

TrackRow = tuple[int, str]


class TrackFormatError(ValueError):
    """Raised when a track row is malformed."""

    def __init__(self, location: str, message: str) -> None:
        """Report ``message`` about ``location``, such as ``row[3]``."""
        super().__init__(f"{location}: {message}")
        self.location = location


class TrackParser:
    """Parses track rows into a :class:`Track`.

    A track is a sequence of ``(count, row)`` pairs: ``row`` is repeated ``count`` times in a row, so a long
    straight is written once. A row is eight whitespace-separated cells: ``..`` for a gap, or a tile letter
    followed by a height digit (``N1``, ``B2``...), optionally followed by either a tunnel letter (``N1T`` for a
    square tunnel, ``N1A`` for a round one) or a slope naming the raised side or corner (``N1f`` rises toward the
    front, ``N1b``, ``N1l`` and ``N1r`` toward the back, left and right, ``N1fl``, ``N1fr``, ``N1bl`` and ``N1br``
    toward one corner). The height digit of a slope is its low side. The first row is the start of the track.
    """

    TRACK = "track"
    GAP = ".."
    MAX_LEVEL = 8
    TUNNELS = frozenset(kind.value for kind in TunnelKind)
    SLOPES = frozenset(slope.value for slope in Slope)

    def parse(self, rows: Sequence[TrackRow], locations: Sequence[str] | None = None) -> Track:
        """Expand and parse ``rows``. Errors name a row by its entry in ``locations``, or as ``row[index]``."""
        grid: list[list[Tile | None]] = []
        for index, entry in enumerate(rows):
            location = locations[index] if locations is not None else f"row[{index}]"
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise TrackFormatError(location, f"expected a (count, row) pair, got {entry!r}")
            count, line = entry
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                raise TrackFormatError(location, f"the count must be a positive integer, got {count!r}")
            if not isinstance(line, str):
                raise TrackFormatError(location, f"a row must be a string, got {line!r}")
            cells = line.split()
            if len(cells) != Track.COLUMNS:
                raise TrackFormatError(location, f"expected {Track.COLUMNS} cells, got {len(cells)}")
            for _ in range(count):
                row = len(grid)
                grid.append([self._parse_cell(location, row, column, cell) for column, cell in enumerate(cells)])
        if not grid:
            raise TrackFormatError(self.TRACK, "the track has no rows")
        return Track(grid)

    def _parse_cell(self, location: str, row: int, column: int, cell: str) -> Tile | None:
        if cell == self.GAP:
            return None
        if len(cell) < 2 or not cell[1].isdigit() or not 1 <= int(cell[1]) <= self.MAX_LEVEL:
            raise TrackFormatError(location, f"invalid cell {cell!r}")
        try:
            tile_type = TileType(cell[0])
        except ValueError:
            raise TrackFormatError(location, f"unknown tile type {cell[0]!r}") from None
        suffix = cell[2:]
        tunnel = slope = None
        if suffix in self.TUNNELS:
            tunnel = TunnelKind(suffix)
        elif suffix in self.SLOPES:
            slope = Slope(suffix)
        elif suffix:
            raise TrackFormatError(location, f"unknown tunnel or slope {suffix!r}")
        return Tile(tile_type, column, row, int(cell[1]), tunnel, slope)
