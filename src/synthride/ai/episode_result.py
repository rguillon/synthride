# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The outcome of one attempt at a level."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EpisodeResult:
    """How one attempt at a level went: how far the ship got, whether it won and how long it took."""

    progress: float
    won: bool
    seconds: float

    @property
    def score(self) -> float:
        """The fitness of the attempt: the progress, plus a bonus for winning that grows with speed."""
        return self.progress + (1.0 + 1.0 / (1.0 + self.seconds / 30)) * self.won
