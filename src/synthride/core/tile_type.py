from enum import Enum


class TileType(Enum):
    """The kinds of track blocks. The value is the letter used in level files."""

    NORMAL = "N"
    BOOST = "B"
    SLOW = "S"
    KILL = "K"
    REFUEL = "R"
    FINISH = "F"
