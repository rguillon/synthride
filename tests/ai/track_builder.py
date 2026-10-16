# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Lays out a track row by row along a safe lane."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from synthride.core.track import Track

if TYPE_CHECKING:
    from tests.ai.track_reach import TrackReach


class TrackBuilder:
    """Writes track rows in :class:`~synthride.core.track_parser.TrackParser` cells, following a safe lane.

    The lane is the run of columns, from ``low`` to ``high``, and the height ``level`` the ship can surely ride.
    The builder also follows the most speed the ship can have, from standstill at the start, as
    :class:`~tests.ai.finishability_checker.FinishabilityChecker` does, so that gaps can be sized to it.
    """

    GAP: ClassVar[str] = ".."
    TOP_LEVEL: ClassVar[int] = 6

    def __init__(self, reach: TrackReach) -> None:
        """Start on columns 3 and 4 at height 1, at standstill, judging speeds with ``reach``."""
        self.reach = reach
        self.rows: list[list[str]] = []
        self.low, self.high, self.level = 3, 4, 1
        self.speed = 0.0

    @property
    def width(self) -> int:
        """How many columns wide the lane is."""
        return self.high - self.low + 1

    @property
    def center(self) -> float:
        """The middle of the lane, in columns."""
        return (self.low + self.high) / 2

    @staticmethod
    def lane_around(center: float, width: int) -> tuple[int, int]:
        """Return the first and last columns of a lane ``width`` columns wide around ``center``, on the track."""
        width = min(Track.COLUMNS, max(1, width))
        low = min(Track.COLUMNS - width, max(0, round(center - (width - 1) / 2)))
        return low, low + width - 1

    def row(self, cells: dict[int, str], *, count: int = 1, slow: bool = False) -> None:
        """Write ``count`` rows with ``cells`` by column, gaps elsewhere; ``slow`` if the ship can only ride slow."""
        line = [cells.get(column, self.GAP) for column in range(Track.COLUMNS)]
        for _ in range(count):
            self.rows.append(list(line))
            cap = self.reach.slow_speed if slow else self.reach.config.max_speed
            self.speed = self.reach.next_speed(self.speed, cap)

    def lane(self, letter: str = "N", *, count: int = 1, suffix: str = "", level: int | None = None) -> None:
        """Write ``count`` rows of ``letter`` tiles over the lane, at ``level`` (the lane's height by default)."""
        cell = f"{letter}{self.level if level is None else level}{suffix}"
        self.row(dict.fromkeys(range(self.low, self.high + 1), cell), count=count, slow=letter == "S")

    def gap(self, count: int) -> None:
        """Write ``count`` empty rows."""
        self.row({}, count=count)

    def move_to(self, low: int, high: int, rows_per_step: int, letter: str = "N") -> None:
        """Move the lane to the columns ``low`` to ``high``, each edge one column at a time.

        Each step writes ``rows_per_step`` rows over both the old and the new lane, so the ship can slide across.
        """
        while (self.low, self.high) != (low, high):
            new_low = self.low + (low > self.low) - (low < self.low)
            new_high = self.high + (high > self.high) - (high < self.high)
            cell = f"{letter}{self.level}"
            union = range(min(self.low, new_low), max(self.high, new_high) + 1)
            self.row(dict.fromkeys(union, cell), count=rows_per_step, slow=letter == "S")
            self.low, self.high = new_low, new_high

    def encoded(self) -> list[list[int | str]]:
        """Return the rows as the ``[count, row]`` pairs of a level file, runs of equal rows merged."""
        counts: list[int] = []
        lines: list[str] = []
        for row in self.rows:
            line = " ".join(row)
            if lines and lines[-1] == line:
                counts[-1] += 1
            else:
                counts.append(1)
                lines.append(line)
        return [[count, line] for count, line in zip(counts, lines, strict=True)]
