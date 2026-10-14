from dataclasses import dataclass


@dataclass(frozen=True)
class ShipInput:
    """The player's commands for one simulation step."""

    accelerate: bool = False
    brake: bool = False
    left: bool = False
    right: bool = False
    jump: bool = False
