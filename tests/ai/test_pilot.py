# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.ai.neural_network import NeuralNetwork
from synthride.ai.pilot import Pilot
from synthride.core.game_session import GameSession
from synthride.core.ship_input import ShipInput
from tests.ai.networks import constant_network
from tests.level_factory import make_level


def decide(network: NeuralNetwork) -> ShipInput:
    session = GameSession([make_level("N1 N1 N1 N1 N1 N1 N1 N1")])
    session.start()
    return Pilot(network).decide(session)


def test_rejects_networks_of_the_wrong_shape() -> None:
    with pytest.raises(ValueError, match="inputs to 3 outputs"):
        Pilot(NeuralNetwork((2, 3), [0.0] * 9))


def test_maps_outputs_to_commands() -> None:
    assert decide(constant_network(1, 1, 1)) == ShipInput(accelerate=True, right=True, jump=True)
    assert decide(constant_network(-1, -1, -1)) == ShipInput(brake=True, left=True)
    assert decide(constant_network(0.1, -0.1, 0)) == ShipInput()
