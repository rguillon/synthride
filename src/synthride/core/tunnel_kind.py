from enum import Enum


class TunnelKind(Enum):
    """The shapes of tunnel that can cover a tile. The value is the suffix used in level files."""

    SQUARE = "T"
    ROUND = "A"
