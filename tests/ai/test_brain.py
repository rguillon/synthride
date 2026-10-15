# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import random

from synthride.ai.brain import Brain
from synthride.ai.neural_network import NeuralNetwork


def test_round_trips_through_a_dict() -> None:
    brain = Brain(NeuralNetwork.random((2, 1), random.Random(1)), generation=3, fitness=1.23456)
    copy = Brain.from_dict(brain.to_dict())
    assert (copy.generation, copy.fitness) == (3, 1.2346)
    assert copy.network.layer_sizes == (2, 1)
