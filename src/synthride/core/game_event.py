# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Events emitted by the game session."""

from enum import Enum, auto


class GameEvent(Enum):
    """Notable things that happened during an update, consumed by sound and visual effects."""

    LEVEL_STARTED = auto()
    JUMPED = auto()
    DOUBLE_JUMPED = auto()
    LANDED = auto()
    BUMPED = auto()
    NUDGED = auto()
    BOOSTED = auto()
    SLOWED = auto()
    REFUELED = auto()
    REFILLED_AIR = auto()
    LAUNCHED = auto()
    SKIDDED = auto()
    PUSHED = auto()
    CRASHED = auto()
    FELL = auto()
    BURNED = auto()
    OUT_OF_FUEL = auto()
    OUT_OF_OXYGEN = auto()
    LIFE_LOST = auto()
    LEVEL_WON = auto()
    GAME_OVER = auto()
    GAME_COMPLETED = auto()
