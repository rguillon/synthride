# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Builds networks for tests."""

from synthride.ai.neural_network import NeuralNetwork
from synthride.ai.pilot import Pilot
from synthride.ai.ship_observer import ShipObserver


def constant_network(throttle: float = 0.0, steering: float = 0.0, jump: float = 0.0) -> NeuralNetwork:
    """Return a pilot network that ignores its inputs, its outputs set by the biases (as tanh pre-activations)."""
    inputs = ShipObserver.SIZE
    weights: list[float] = []
    for bias in (throttle, steering, jump):
        weights += [bias] + [0.0] * inputs
    return NeuralNetwork((inputs, Pilot.OUTPUTS), weights)
