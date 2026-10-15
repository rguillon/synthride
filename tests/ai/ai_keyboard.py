# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""A keyboard whose ship controls are held by the neural network."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar

from synthride.core.game_config import GameConfig
from synthride.core.game_phase import GamePhase
from synthride.core.ship_input import ShipInput
from synthride.web.browser_keyboard import BrowserKeyboard
from tests.ai.episode_runner import EpisodeRunner
from tests.ai.pilot import Pilot

if TYPE_CHECKING:
    from synthride.core.game_session import GameSession
    from synthride.core.ship import Ship
    from synthride.web.js_bridge import JsBridge
    from tests.ai.neural_network import NeuralNetwork


class AiKeyboard(BrowserKeyboard):
    """Leaves the menus to the player's keys but steers the ship with a network.

    A fresh pilot takes each attempt, recognised by its new ship, and decides about as often as in training.
    """

    DECISION_SECONDS: ClassVar[float] = (
        sum(EpisodeRunner.STEPS_PER_DECISION) / len(EpisodeRunner.STEPS_PER_DECISION) * GameConfig().fixed_step
    )

    def __init__(self, bridge: JsBridge, session: GameSession, network: NeuralNetwork) -> None:
        """Steer the ship of ``session`` with ``network``."""
        super().__init__(bridge)
        self._clock = bridge.window.performance
        self._session = session
        self._network = network
        self._ship: Ship | None = None
        self._pilot = Pilot(network)
        self._input = ShipInput()
        self._decided_at = -math.inf

    def ship_input(self) -> ShipInput:
        """Return the network's latest commands, deciding again when it is time."""
        session = self._session
        if session.phase is not GamePhase.PLAYING:
            return ShipInput()
        if session.ship is not self._ship:
            self._ship, self._pilot, self._decided_at = session.ship, Pilot(self._network), -math.inf
        now = self._clock.now() / 1000
        if now - self._decided_at >= self.DECISION_SECONDS:
            self._input, self._decided_at = self._pilot.decide(session), now
        return self._input
