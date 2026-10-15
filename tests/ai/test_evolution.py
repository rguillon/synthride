# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import random

import pytest

from synthride.ai.evolution import Evolution
from synthride.ai.neural_network import NeuralNetwork


def test_rejects_bad_elite_counts() -> None:
    with pytest.raises(ValueError, match="elite_count"):
        Evolution(4, 4, 0.1, random.Random(1))
    with pytest.raises(ValueError, match="elite_count"):
        Evolution(4, 0, 0.1, random.Random(1))


def test_seeds_random_networks() -> None:
    population = Evolution(5, 2, 0.1, random.Random(1)).seed((3, 2))
    assert len(population) == 5
    assert len({tuple(network.weights) for network in population}) == 5


def test_seeds_mutants_of_an_ancestor() -> None:
    ancestor = NeuralNetwork.random((3, 2), random.Random(1))
    population = Evolution(5, 2, 0.1, random.Random(1)).seed((3, 2), ancestor)
    assert population[0] is ancestor
    assert all(network.weights != ancestor.weights for network in population[1:])


def test_keeps_the_elites_and_breeds_the_rest_from_them() -> None:
    evolution = Evolution(4, 2, 0.0, random.Random(1))
    population = evolution.seed((3, 2))
    children = evolution.next_generation(population, [1.0, 4.0, 3.0, 2.0])
    assert children[:2] == [population[1], population[2]]
    assert len(children) == 4
    assert all(child.weights in (population[1].weights, population[2].weights) for child in children[2:])
