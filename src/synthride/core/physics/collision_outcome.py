# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The outcomes of moving the ship through the track."""

from enum import Enum, auto


class CollisionOutcome(Enum):
    """What happened to the ship while it moved during one step."""

    LANDED = auto()
    BUMPED = auto()
    NUDGED = auto()
    SCRAPED_LEFT = auto()
    SCRAPED_RIGHT = auto()
    CRASHED = auto()
    FELL = auto()
