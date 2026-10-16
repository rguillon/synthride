# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The editable grid of a track, and the brushes that paint it."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

from synthride.core.world.level import Level
from synthride.core.world.level_parser import LevelParser
from synthride.core.world.track import Track
from synthride.core.world.track_parser import TrackParser

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from synthride.core.world.tile import Tile

Cell = str | None
"""A cell as written in level files (``N1``, ``I2f``, ``K1T``...), None for a gap."""


class BrushKind(Enum):
    """What a brush does to the cells it covers."""

    TILE = "tile"  # lay tiles of one type
    ERASE = "erase"  # leave gaps
    RAISE = "raise"  # one height up
    LOWER = "lower"  # one height down
    SHAPE = "shape"  # a slope or a tunnel, or neither: flat and open


@dataclass(frozen=True)
class Brush:
    """A brush of ``kind``. ``value`` is the tile letter of a tile brush, or the suffix a shape brush gives.

    A shape suffix is a slope (``f``, ``b``...), a tunnel (``T``, ``A``), or empty for flat and open tiles.
    """

    kind: BrushKind
    value: str = ""


@dataclass(frozen=True)
class Rect:
    """The cells between two corner cells, both included, the corners given in either order."""

    column: int
    row: int
    other_column: int
    other_row: int

    @property
    def columns(self) -> range:
        """The columns covered, from left to right."""
        return range(min(self.column, self.other_column), max(self.column, self.other_column) + 1)

    @property
    def rows(self) -> range:
        """The rows covered, from the start onward."""
        return range(min(self.row, self.other_row), max(self.row, self.other_row) + 1)

    def cells(self) -> Iterator[tuple[int, int]]:
        """Yield the ``(column, row)`` of each cell covered."""
        for row in self.rows:
            for column in self.columns:
                yield column, row


class TrackGrid:
    """A track being edited: rows of eight cells from the start, which brushes paint over rectangles.

    Painting a tile over a tile keeps its height and shape and changes its type; painting over a gap lays a tile at
    the brush height. Painting past the last row makes the track longer; gaps at the end are dropped when the track
    is saved. Each paint can be undone.
    """

    MAX_ROWS: ClassVar[int] = 2000
    UNDO_DEPTH: ClassVar[int] = 100

    def __init__(self, rows: Sequence[Sequence[Cell]] = ()) -> None:
        """Edit ``rows`` of eight cells each."""
        self._rows: list[list[Cell]] = [list(row) for row in rows]
        self._history: list[list[list[Cell]]] = []

    @classmethod
    def starter(cls) -> TrackGrid:
        """Return a short straight, four tiles wide, with a finish line: a track to start from."""
        lane = [None, None, "N1", "N1", "N1", "N1", None, None]
        finish = [None, None, "F1", "F1", "F1", "F1", None, None]
        return cls([lane] * 30 + [finish] * 3)

    @classmethod
    def from_track(cls, track: Track) -> TrackGrid:
        """Return the grid of ``track``."""
        return cls([
            [cls.cell_of(track.tile_at(column, row)) for column in range(Track.COLUMNS)]
            for row in range(track.row_count)
        ])

    @staticmethod
    def cell_of(tile: Tile | None) -> Cell:
        """Return ``tile`` written as a cell."""
        if tile is None:
            return None
        suffix = tile.tunnel.value if tile.tunnel else tile.slope.value if tile.slope else ""
        return f"{tile.tile_type.value}{tile.level}{suffix}"

    @property
    def row_count(self) -> int:
        """How many rows the grid holds, gaps at the end included."""
        return len(self._rows)

    @property
    def length(self) -> int:
        """How many rows the track has, up to its last tile."""
        for index in range(len(self._rows) - 1, -1, -1):
            if any(self._rows[index]):
                return index + 1
        return 0

    @property
    def can_undo(self) -> bool:
        """Whether there is a paint to undo."""
        return bool(self._history)

    def cell(self, column: int, row: int) -> Cell:
        """Return the cell at ``(column, row)``, None past the edges."""
        if 0 <= column < Track.COLUMNS and 0 <= row < len(self._rows):
            return self._rows[row][column]
        return None

    def paint(self, rect: Rect, brush: Brush, height: int = 1) -> bool:
        """Paint ``rect`` with ``brush``, new tiles at ``height``. Return whether any cell changed."""
        rows = [list(row) for row in self._rows]
        last = min(max(rect.rows), self.MAX_ROWS - 1)
        while len(rows) <= last and brush.kind is BrushKind.TILE:
            rows.append([None] * Track.COLUMNS)
        height = min(TrackParser.MAX_LEVEL, max(1, height))
        changed = False
        for column, row in rect.cells():
            if not (0 <= column < Track.COLUMNS and 0 <= row < len(rows)):
                continue
            cell = self._painted(rows[row][column], brush, height)
            if cell != rows[row][column]:
                rows[row][column] = cell
                changed = True
        if changed:
            self._history.append(self._rows)
            del self._history[: -self.UNDO_DEPTH]
            self._rows = rows
        return changed

    def undo(self) -> None:
        """Undo the last paint."""
        if self._history:
            self._rows = self._history.pop()

    @classmethod
    def _painted(cls, cell: Cell, brush: Brush, height: int) -> Cell:
        """Return ``cell`` once ``brush`` went over it."""
        kind = brush.kind
        if kind is BrushKind.ERASE:
            return None
        if kind is BrushKind.TILE:
            if cell is None:
                return f"{brush.value}{height}"
            return f"{brush.value}{cell[1:]}"
        if cell is None:
            return None
        level, suffix = int(cell[1]), cell[2:]
        if kind is BrushKind.RAISE:
            level = min(TrackParser.MAX_LEVEL, level + 1)
        elif kind is BrushKind.LOWER:
            level = max(1, level - 1)
        else:
            suffix = brush.value
        return f"{cell[0]}{level}{suffix}"

    def rows(self) -> list[str]:
        """Return the track's rows, up to its last tile, as written in level files; one gap row if it is empty."""
        rows = [" ".join(cell or TrackParser.GAP for cell in row) for row in self._rows[: self.length]]
        return rows or [" ".join([TrackParser.GAP] * Track.COLUMNS)]

    def encoded(self) -> list[list[int | str]]:
        """Return the rows as the ``[count, row]`` pairs of a level file, runs of equal rows merged."""
        pairs: list[list[int | str]] = []
        for line in self.rows():
            if pairs and pairs[-1][1] == line:
                pairs[-1][0] = int(pairs[-1][0]) + 1
            else:
                pairs.append([1, line])
        return pairs

    def track(self) -> Track:
        """Return the track the grid makes."""
        return TrackParser().parse([(1, line) for line in self.rows()])


@dataclass(frozen=True)
class LevelSettings:
    """Everything of a level but its track."""

    name: str = "My track"
    gravity: float = 18.0
    oxygen_seconds: float = 90.0
    fuel_capacity: float = 100.0

    def level(self, grid: TrackGrid) -> Level:
        """Return the level of ``grid`` with these settings."""
        return Level(self.name, grid.track(), self.gravity, self.oxygen_seconds, self.fuel_capacity)

    def document(self, grid: TrackGrid) -> dict[str, Any]:
        """Return the level file of ``grid`` with these settings, as a JSON object."""
        return {
            "name": self.name,
            "gravity": self.gravity,
            "oxygen": self.oxygen_seconds,
            "fuel": self.fuel_capacity,
            "track": grid.encoded(),
        }

    @classmethod
    def of(cls, level: Level) -> LevelSettings:
        """Return the settings of ``level``."""
        return cls(level.name, level.gravity, level.oxygen_seconds, level.fuel_capacity)

    @classmethod
    def read(cls, text: str) -> tuple[LevelSettings, TrackGrid]:
        """Return the settings and grid of the level file ``text``. Raise ``ValueError`` if it is not one."""
        level = LevelParser().parse(text)
        return cls.of(level), TrackGrid.from_track(level.track)

    def write(self, grid: TrackGrid) -> str:
        """Return the level file of ``grid`` with these settings."""
        return json.dumps(self.document(grid), indent=2, ensure_ascii=False)
