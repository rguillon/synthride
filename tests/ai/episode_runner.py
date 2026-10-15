# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Plays one life of one level with a pilot."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, ClassVar

from synthride.core.game_event import GameEvent
from synthride.core.game_phase import GamePhase
from synthride.core.game_session import GameSession
from synthride.core.vector3 import Vector3
from tests.ai.episode_result import EpisodeResult

if TYPE_CHECKING:
    from collections.abc import Sequence

    from synthride.core.level import Level
    from tests.ai.pilot import Pilot


class EpisodeRunner:
    """Runs a pilot on a level until it wins, loses its life or stops making progress.

    The pilot decides every few simulation steps. A seeded random generator shifts the start position and the
    decision rhythm a little, so that different seeds give different, reproducible, attempts.
    """

    STEPS_PER_DECISION: ClassVar[tuple[int, ...]] = (5, 6, 7)
    START_JITTER: ClassVar[float] = 0.15
    STALL_SECONDS: ClassVar[float] = 3.0
    STALL_DISTANCE: ClassVar[float] = 1.0

    def __init__(self, levels: Sequence[Level]) -> None:
        """Play the levels of ``levels``."""
        self._session = GameSession(levels)

    def run(self, pilot: Pilot, level_index: int, seed: int) -> EpisodeResult:
        """Play the level at ``level_index`` with ``pilot`` and return how it went."""
        session = self._session
        rng = random.Random(seed)
        session.selected_level = level_index
        session.start()
        ship = session.ship
        ship.position = ship.position + Vector3(rng.uniform(-self.START_JITTER, self.START_JITTER), 0.0, 0.0)
        step = session.config.fixed_step
        seconds = stall_seconds = 0.0
        best_z = ship.position.z
        while session.phase is GamePhase.PLAYING:
            steps = rng.choice(self.STEPS_PER_DECISION)
            if GameEvent.LEVEL_WON in session.update(steps * step, pilot.decide(session)):
                return EpisodeResult(1.0, won=True, seconds=seconds + steps * step)
            seconds += steps * step
            stall_seconds += steps * step
            if session.ship.position.z > best_z + self.STALL_DISTANCE:
                best_z, stall_seconds = session.ship.position.z, 0.0
            elif stall_seconds > self.STALL_SECONDS:
                break
        return EpisodeResult(session.progress, won=False, seconds=seconds)
