from __future__ import annotations

from typing import ClassVar

from synthride.core.level import Level
from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.core.track import Track


class LevelFormatError(ValueError):
    """Raised when a level file is malformed."""

    def __init__(self, line_number: int, message: str) -> None:
        super().__init__(f"line {line_number}: {message}")
        self.line_number = line_number


class LevelParser:
    """Parses the text level format.

    A header of ``key: value`` lines ends with ``---``. Each following line is one track row of eight
    whitespace-separated cells: ``..`` for a gap, or a tile letter followed by a height digit (``N1``,
    ``B2``...). The first row is the start of the track. ``#`` starts a comment.
    """

    SEPARATOR = "---"
    GAP = ".."
    MAX_LEVEL = 4
    NUMERIC_KEYS: ClassVar[dict[str, str]] = {"gravity": "gravity", "oxygen": "oxygen_seconds", "fuel": "fuel_capacity"}

    def parse(self, text: str) -> Level:
        lines = list(enumerate(text.splitlines(), start=1))
        separator_index = next(
            (index for index, (_, line) in enumerate(lines) if self._strip(line) == self.SEPARATOR), None
        )
        if separator_index is None:
            raise LevelFormatError(len(lines), f"missing '{self.SEPARATOR}' header separator")
        settings = self._parse_header(lines[:separator_index])
        rows: list[list[Tile | None]] = []
        for number, line in lines[separator_index + 1 :]:
            if stripped := self._strip(line):
                rows.append(self._parse_row(number, len(rows), stripped))
        if not rows:
            raise LevelFormatError(len(lines), "the track has no rows")
        return Level(track=Track(rows), **settings)

    def _strip(self, line: str) -> str:
        return line.split("#", 1)[0].strip()

    def _parse_header(self, lines: list[tuple[int, str]]) -> dict:
        settings: dict = {"name": "Untitled"}
        for number, line in lines:
            stripped = self._strip(line)
            if not stripped:
                continue
            key, colon, value = (part.strip() for part in stripped.partition(":"))
            if not colon:
                raise LevelFormatError(number, f"expected 'key: value', got {stripped!r}")
            if key == "name":
                settings["name"] = value
            elif key in self.NUMERIC_KEYS:
                try:
                    settings[self.NUMERIC_KEYS[key]] = float(value)
                except ValueError:
                    raise LevelFormatError(number, f"{key} must be a number, got {value!r}") from None
            else:
                raise LevelFormatError(number, f"unknown header key {key!r}")
        return settings

    def _parse_row(self, number: int, row: int, line: str) -> list[Tile | None]:
        cells = line.split()
        if len(cells) != Track.COLUMNS:
            raise LevelFormatError(number, f"expected {Track.COLUMNS} cells, got {len(cells)}")
        return [self._parse_cell(number, row, column, cell) for column, cell in enumerate(cells)]

    def _parse_cell(self, number: int, row: int, column: int, cell: str) -> Tile | None:
        if cell == self.GAP:
            return None
        if len(cell) != 2 or not cell[1].isdigit() or not 1 <= int(cell[1]) <= self.MAX_LEVEL:
            raise LevelFormatError(number, f"invalid cell {cell!r}")
        try:
            tile_type = TileType(cell[0])
        except ValueError:
            raise LevelFormatError(number, f"unknown tile type {cell[0]!r}") from None
        return Tile(tile_type, column, row, int(cell[1]))
