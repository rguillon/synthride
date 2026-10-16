# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.gameplay.game_phase import GamePhase


def test_phases() -> None:
    assert GamePhase.TITLE in GamePhase
    assert len(GamePhase) == 8
