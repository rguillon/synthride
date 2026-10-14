from enum import Enum, auto


class CollisionOutcome(Enum):
    """What happened to the ship while it moved during one step."""

    LANDED = auto()
    NUDGED = auto()
    CRASHED = auto()
    FELL = auto()
