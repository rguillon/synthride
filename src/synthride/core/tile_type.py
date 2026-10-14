# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The kinds of track tiles."""

from enum import Enum


class TileType(Enum):
    """The kinds of track blocks. The value is the letter used in level files."""

    NORMAL = "N"
    BOOST = "B"
    SLOW = "S"
    KILL = "K"
    REFUEL = "R"
    AIR = "O"
    JUMP = "J"
    ICE = "I"
    PUSH_LEFT = "<"
    PUSH_RIGHT = ">"
    FINISH = "F"
