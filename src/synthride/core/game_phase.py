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
