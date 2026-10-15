# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Drives the ship with a neural network."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from synthride.core.ship_input import ShipInput
from tests.ai.ship_observer import ShipObserver

if TYPE_CHECKING:
    from synthride.core.game_session import GameSession
    from tests.ai.neural_network import NeuralNetwork


class Pilot:
    """Turns the network's three outputs (throttle, steering, jump) into the ship's commands.

    Throttle and steering act past ``DEAD_ZONE`` either way; jump is pressed when its output is positive.
    """

    OUTPUTS: ClassVar[int] = 3
    DEAD_ZONE: ClassVar[float] = 0.3

    def __init__(self, network: NeuralNetwork, observer: ShipObserver | None = None) -> None:
        """Drive with ``network``, which must take ``observer.SIZE`` inputs and give ``OUTPUTS`` outputs."""
        self._observer = observer or ShipObserver()
        sizes = network.layer_sizes
        if sizes[0] != self._observer.SIZE or sizes[-1] != self.OUTPUTS:
            msg = f"the network must map {self._observer.SIZE} inputs to {self.OUTPUTS} outputs"
            raise ValueError(msg)
        self._network = network

    def decide(self, session: GameSession) -> ShipInput:
        """Return the commands for the session's current state."""
        throttle, steering, jump = self._network.forward(self._observer.observe(session))
        return ShipInput(
            accelerate=throttle > self.DEAD_ZONE,
            brake=throttle < -self.DEAD_ZONE,
            left=steering < -self.DEAD_ZONE,
            right=steering > self.DEAD_ZONE,
            jump=jump > 0,
        )
