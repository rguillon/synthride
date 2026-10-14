# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Parsing of the JSON level format."""

from __future__ import annotations

import json
from typing import ClassVar

from synthride.core.level import Level
from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.core.track import Track
from synthride.core.tunnel_kind import TunnelKind


class LevelFormatError(ValueError):
    """Raised when a level file is malformed."""

    def __init__(self, location: str, message: str) -> None:
        """Report ``message`` about ``location``, such as ``line 3`` or ``track[12]``."""
        super().__init__(f"{location}: {message}")
        self.location = location


class LevelParser:
    """Parses the JSON level format.

    A level is a JSON object with an optional ``name``, ``gravity``, ``oxygen`` and ``fuel``, and a ``track``
    list of strings. Each string is one track row of eight whitespace-separated cells: ``..`` for a gap, or a
    tile letter followed by a height digit (``N1``, ``B2``...), optionally followed by a tunnel letter (``N1T``
    for a square tunnel, ``N1A`` for a round one). The first row is the start of the track. ``#`` starts a
    comment, so a string starting with ``#`` is a comment line.
    """

    LEVEL = "level"
    TRACK = "track"
    GAP = ".."
    MAX_LEVEL = 4
    NUMERIC_KEYS: ClassVar[dict[str, str]] = {"gravity": "gravity", "oxygen": "oxygen_seconds", "fuel": "fuel_capacity"}

    def parse(self, text: str) -> Level:
        """Parse the text of a level file."""
        try:
            document = json.loads(text)
        except json.JSONDecodeError as error:
            location = f"line {error.lineno}"
            raise LevelFormatError(location, f"invalid JSON: {error.msg}") from None
        if not isinstance(document, dict):
            raise LevelFormatError(self.LEVEL, "a level must be a JSON object")
        settings: dict = {"name": "Untitled"}
        for key, value in document.items():
            if key == "name":
                if not isinstance(value, str):
                    raise LevelFormatError(key, f"must be a string, got {value!r}")
                settings["name"] = value
            elif key in self.NUMERIC_KEYS:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise LevelFormatError(key, f"must be a number, got {value!r}")
                settings[self.NUMERIC_KEYS[key]] = float(value)
            elif key != self.TRACK:
                raise LevelFormatError(key, "unknown key")
        if self.TRACK not in document:
            raise LevelFormatError(self.LEVEL, "missing 'track'")
        return Level(track=self._parse_track(document[self.TRACK]), **settings)

    def _parse_track(self, track: object) -> Track:
        if not isinstance(track, list):
            raise LevelFormatError(self.TRACK, "must be a list of rows")
        rows: list[list[Tile | None]] = []
        for index, line in enumerate(track):
            location = f"track[{index}]"
            if not isinstance(line, str):
                raise LevelFormatError(location, f"a row must be a string, got {line!r}")
            if stripped := line.split("#", 1)[0].strip():
                rows.append(self._parse_row(location, len(rows), stripped))
        if not rows:
            raise LevelFormatError(self.TRACK, "the track has no rows")
        return Track(rows)

    def _parse_row(self, location: str, row: int, line: str) -> list[Tile | None]:
        cells = line.split()
        if len(cells) != Track.COLUMNS:
            raise LevelFormatError(location, f"expected {Track.COLUMNS} cells, got {len(cells)}")
        return [self._parse_cell(location, row, column, cell) for column, cell in enumerate(cells)]

    def _parse_cell(self, location: str, row: int, column: int, cell: str) -> Tile | None:
        if cell == self.GAP:
            return None
        if len(cell) not in (2, 3) or not cell[1].isdigit() or not 1 <= int(cell[1]) <= self.MAX_LEVEL:
            raise LevelFormatError(location, f"invalid cell {cell!r}")
        try:
            tile_type = TileType(cell[0])
        except ValueError:
            raise LevelFormatError(location, f"unknown tile type {cell[0]!r}") from None
        try:
            tunnel = TunnelKind(cell[2]) if len(cell) == 3 else None
        except ValueError:
            raise LevelFormatError(location, f"unknown tunnel kind {cell[2]!r}") from None
        return Tile(tile_type, column, row, int(cell[1]), tunnel)
