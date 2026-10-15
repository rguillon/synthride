# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import math
import random

import pytest

from synthride.ai.neural_network import NeuralNetwork


def test_weight_count_includes_biases() -> None:
    assert NeuralNetwork.weight_count((3, 2, 1)) == 4 * 2 + 3 * 1


def test_rejects_bad_shapes() -> None:
    with pytest.raises(ValueError, match="at least"):
        NeuralNetwork((3,), [])
    with pytest.raises(ValueError, match="expected 3 weights"):
        NeuralNetwork((2, 1), [0.0])


def test_forward_applies_bias_weights_and_tanh_per_layer() -> None:
    network = NeuralNetwork((2, 1, 1), [0.5, 1.0, -2.0, 0.0, 2.0])
    hidden = math.tanh(0.5 + 1.0 * 3 - 2.0 * 1)
    assert network.forward([3, 1]) == [pytest.approx(math.tanh(2.0 * hidden))]


def test_random_networks_have_zero_biases_and_are_reproducible() -> None:
    network = NeuralNetwork.random((4, 2), random.Random(1))
    assert network.weights[0] == network.weights[5] == 0.0
    assert network.weights == NeuralNetwork.random((4, 2), random.Random(1)).weights
    assert any(weight != 0 for weight in network.weights)


def test_mutation_returns_a_noisy_copy() -> None:
    network = NeuralNetwork.random((4, 2), random.Random(1))
    mutant = network.mutated(0.1, random.Random(2))
    assert mutant.layer_sizes == network.layer_sizes
    assert mutant.weights != network.weights
    assert all(abs(a - b) < 1 for a, b in zip(mutant.weights, network.weights, strict=True))


def test_round_trips_through_a_dict() -> None:
    network = NeuralNetwork.random((4, 3, 2), random.Random(1))
    copy = NeuralNetwork.from_dict(network.to_dict())
    assert copy.layer_sizes == network.layer_sizes
    assert copy.weights == pytest.approx(network.weights, abs=1e-6)
