# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json

import numpy as np

from tests.ai.level_evaluator import LevelEvaluator
from tests.ai.level_generator import LevelGenerator
from tests.ai.neural_network import NeuralNetwork
from tests.ai.pilot import Pilot


def test_plays_a_level_given_as_text() -> None:
    sizes = (Pilot.INPUTS, Pilot.OUTPUTS)
    network = NeuralNetwork(sizes, np.zeros(NeuralNetwork.weight_count(sizes)))
    text = json.dumps(LevelGenerator(2).build([None]))
    with LevelEvaluator() as evaluator:
        results = evaluator.play_level(network, text, [1, 2, 3])
        again = evaluator.play_level(network, text, [1, 2, 3])
        evaluator.play_level(network, json.dumps(LevelGenerator(3).build([None, None])), [1])
        evaluator.play_level(network, json.dumps(LevelGenerator(4).build([None, None, None])), [1])
    assert len(results) == 3
    assert results == again
    assert all(not result.won for result in results)
