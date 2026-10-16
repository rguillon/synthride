# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Drives the ship with a neural network."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np

from synthride.core.ship_input import ShipInput
from tests.ai.ship_observer import ShipObserver

if TYPE_CHECKING:
    from synthride.core.game_session import GameSession
    from tests.ai.neural_network import NeuralNetwork


class Pilot:
    """Turns the network's three outputs (throttle, steering, jump) into the ship's commands.

    Throttle and steering act past ``DEAD_ZONE`` either way; jump is pressed when its output is positive.
    The network sees the observer's inputs followed by its own outputs from the previous decision, zero at first,
    so it can keep to a course of action. A pilot therefore drives a single attempt.
    """

    OUTPUTS: ClassVar[int] = 3
    INPUTS: ClassVar[int] = ShipObserver.SIZE + OUTPUTS
    DEAD_ZONE: ClassVar[float] = 0.3

    def __init__(self, network: NeuralNetwork, observer: ShipObserver | None = None) -> None:
        """Drive with ``network``, which must take ``INPUTS`` inputs and give ``OUTPUTS`` outputs."""
        self._observer = observer or ShipObserver()
        sizes = network.layer_sizes
        if sizes[0] != self.INPUTS or sizes[-1] != self.OUTPUTS:
            msg = f"the network must map {self.INPUTS} inputs to {self.OUTPUTS} outputs"
            raise ValueError(msg)
        self._network = network
        self._previous = np.zeros(self.OUTPUTS)

    def decide(self, session: GameSession) -> ShipInput:
        """Return the commands for the session's current state."""
        outputs = self._network.forward(np.concatenate((self._observer.observe(session), self._previous)))
        self._previous = np.asarray(outputs)
        throttle, steering, jump = outputs
        return ShipInput(
            accelerate=throttle > self.DEAD_ZONE,
            brake=throttle < -self.DEAD_ZONE,
            left=steering < -self.DEAD_ZONE,
            right=steering > self.DEAD_ZONE,
            jump=jump > 0,
        )
