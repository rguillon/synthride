# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The parameters of a generated level, from one difficulty knob."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DifficultyKnobs:
    """Turns the knob ``level``, from 0 (easiest) to 1 (hardest), into the generator's parameters.

    Each parameter also takes a ``draw`` from 0 to 1, a random number the generator picks once per segment whatever
    the knob, so that one layout varies from segment to segment yet every parameter only gets harder as the knob
    turns up.
    """

    level: float

    def __post_init__(self) -> None:
        """Check the knob lies between 0 and 1."""
        if not 0.0 <= self.level <= 1.0:
            msg = f"the difficulty knob goes from 0 to 1, got {self.level}"
            raise ValueError(msg)

    def _lerp(self, easy: float, hard: float) -> float:
        return easy + (hard - easy) * self.level

    def active(self, draw: float) -> bool:
        """Return True if a segment of ``draw`` is an obstacle, rather than a plain straight on easy levels."""
        return draw < self._lerp(0.85, 1.0)

    def lane_width(self, draw: float) -> int:
        """Return how many columns wide the safe lane of a segment is."""
        return min(8, max(1, round(self._lerp(7.0, 2.0) + 3.0 * (draw - 0.5))))

    def gap_share(self, draw: float) -> float:
        """Return how much of the longest jump the ship can surely make a gap takes, from 0 to 1."""
        return self.level * (0.5 + 0.5 * draw)

    def rest_rows(self, draw: float) -> int:
        """Return how many plain rows follow a segment to recover."""
        return max(1, round(self._lerp(5.0, 1.0) * (0.5 + draw)))

    def section_rows(self, draw: float) -> int:
        """Return how many rows a section of ice, pushers, slow tiles or tunnel lasts."""
        return max(2, round(self._lerp(4.0, 14.0) * (0.6 + 0.8 * draw)))

    def shift_rows(self) -> int:
        """Return over how many rows the lane moves one column sideways."""
        return max(1, round(self._lerp(3.0, 1.0)))

    def bend(self, draw: float) -> int:
        """Return by how many columns a bend moves the lane."""
        return 1 + int(draw * self._lerp(1.0, 4.0))

    def height_change(self, draw: float) -> int:
        """Return by how many levels a climb or a drop changes the height."""
        return 1 + int(draw * self._lerp(1.0, 3.0))

    def rises(self, draw: float) -> bool:
        """Return True if the landing of a gap of ``draw`` is higher than its take-off."""
        return draw < self._lerp(0.0, 0.5)

    def kill_rows(self, draw: float) -> int:
        """Return how many rows a strip of kill tiles lasts."""
        return 1 + int(draw * self._lerp(1.0, 4.0))

    @property
    def fuel_slack(self) -> float:
        """How much more fuel than it surely needs the level gives."""
        return self._lerp(2.0, 1.2)

    @property
    def oxygen_slack(self) -> float:
        """How much more oxygen than it surely needs the level gives."""
        return self._lerp(1.8, 1.05)
