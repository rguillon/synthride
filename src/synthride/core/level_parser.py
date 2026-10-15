# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Parsing of the JSON level format."""

from __future__ import annotations

import json
from typing import ClassVar

from synthride.core.level import Level
from synthride.core.track_parser import TrackFormatError, TrackParser, TrackRow


class LevelFormatError(ValueError):
    """Raised when a level file is malformed."""

    def __init__(self, location: str, message: str) -> None:
        """Report ``message`` about ``location``, such as ``line 3`` or ``track[12]``."""
        super().__init__(f"{location}: {message}")
        self.location = location


class LevelParser:
    """Parses the JSON level format.

    A level is a JSON object with an optional ``name``, ``gravity``, ``oxygen`` and ``fuel``, and a ``track``
    list, from the start of the track. Each entry is a ``[count, row]`` pair repeating ``row`` ``count`` times, or
    a lone ``row`` string for a single row; rows are written as :class:`TrackParser` reads them. ``#`` starts a
    comment, so a string starting with ``#`` is a comment line, and blank strings are skipped.
    """

    LEVEL = "level"
    TRACK = "track"
    COMMENT = "#"
    NUMERIC_KEYS: ClassVar[dict[str, str]] = {"gravity": "gravity", "oxygen": "oxygen_seconds", "fuel": "fuel_capacity"}

    def __init__(self, track_parser: TrackParser | None = None) -> None:
        """Parse tracks with ``track_parser``."""
        self._track_parser = track_parser or TrackParser()

    def parse(self, text: str) -> Level:
        """Parse the text of a level file."""
        try:
            document = json.loads(text)
        except json.JSONDecodeError as error:
            location, message = f"line {error.lineno}", f"invalid JSON: {error.msg}"
            raise LevelFormatError(location, message) from None
        if not isinstance(document, dict):
            raise LevelFormatError(self.LEVEL, "a level must be a JSON object")
        settings = self._settings(document)
        if self.TRACK not in document:
            raise LevelFormatError(self.LEVEL, f"missing {self.TRACK!r}")
        rows, locations = self._rows(document[self.TRACK])
        try:
            track = self._track_parser.parse(rows, locations)
        except TrackFormatError as error:
            raise LevelFormatError(error.location, str(error).removeprefix(f"{error.location}: ")) from None
        return Level(track=track, **settings)

    def _settings(self, document: dict) -> dict:
        """Return the level's settings, as :class:`Level` arguments, from every key but the track."""
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
        return settings

    def _rows(self, track: object) -> tuple[list[TrackRow], list[str]]:
        """Return the track's rows as ``(count, row)`` pairs, comments left out, and where each one came from."""
        if not isinstance(track, list):
            raise LevelFormatError(self.TRACK, "must be a list of rows")
        rows: list[TrackRow] = []
        locations: list[str] = []
        for index, entry in enumerate(track):
            location = f"{self.TRACK}[{index}]"
            if isinstance(entry, str):
                count, line = 1, entry
            elif isinstance(entry, list) and len(entry) == 2:
                count, line = entry
            else:
                raise LevelFormatError(location, f"expected a row or a [count, row] pair, got {entry!r}")
            if isinstance(line, str):
                line = line.split(self.COMMENT, 1)[0].strip()
                if not line and isinstance(entry, str):
                    continue
            rows.append((count, line))
            locations.append(location)
        return rows, locations
