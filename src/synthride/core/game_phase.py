# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The phases of the game session."""

from enum import Enum, auto


class GamePhase(Enum):
    """The states of the game session."""

    TITLE = auto()
    LEVEL_SELECT = auto()
    PLAYING = auto()
    DYING = auto()
    LEVEL_WON = auto()
    GAME_OVER = auto()
    VICTORY = auto()
