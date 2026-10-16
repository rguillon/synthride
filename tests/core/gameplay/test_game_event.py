# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.gameplay.game_event import GameEvent


def test_contains_death_causes() -> None:
    assert {"CRASHED", "FELL", "BURNED", "OUT_OF_FUEL", "OUT_OF_OXYGEN"} <= {event.name for event in GameEvent}
