# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""A small fully connected neural network in pure Python."""

from __future__ import annotations

import itertools
import math
import operator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence
    from random import Random


class NeuralNetwork:
    """A multilayer perceptron with tanh activations, its weights kept in one flat list.

    Each layer stores, for every output neuron, its bias followed by one weight per input.
    """

    def __init__(self, layer_sizes: Sequence[int], weights: Sequence[float]) -> None:
        """Build a network with ``layer_sizes`` neurons per layer (inputs first) from its flat ``weights``."""
        self.layer_sizes = tuple(layer_sizes)
        if len(self.layer_sizes) < 2:
            msg = "a network needs at least an input and an output layer"
            raise ValueError(msg)
        if len(weights) != self.weight_count(self.layer_sizes):
            msg = f"expected {self.weight_count(self.layer_sizes)} weights, got {len(weights)}"
            raise ValueError(msg)
        self.weights = list(weights)
        self._layers: list[list[tuple[float, list[float]]]] = []
        start = 0
        for inputs, outputs in itertools.pairwise(self.layer_sizes):
            neurons = []
            for _ in range(outputs):
                neurons.append((self.weights[start], self.weights[start + 1 : start + 1 + inputs]))
                start += 1 + inputs
            self._layers.append(neurons)

    @staticmethod
    def weight_count(layer_sizes: Sequence[int]) -> int:
        """Return the number of weights, biases included, of a network with ``layer_sizes``."""
        return sum((inputs + 1) * outputs for inputs, outputs in itertools.pairwise(layer_sizes))

    @classmethod
    def random(cls, layer_sizes: Sequence[int], rng: Random) -> NeuralNetwork:
        """Create a network with small random weights scaled to each layer's fan-in, and zero biases."""
        weights: list[float] = []
        for inputs, outputs in itertools.pairwise(layer_sizes):
            scale = 1 / math.sqrt(inputs)
            for _ in range(outputs):
                weights.append(0.0)
                weights.extend(rng.gauss(0.0, scale) for _ in range(inputs))
        return cls(layer_sizes, weights)

    def mutated(self, sigma: float, rng: Random) -> NeuralNetwork:
        """Return a copy with gaussian noise of standard deviation ``sigma`` added to every weight."""
        return NeuralNetwork(self.layer_sizes, [weight + rng.gauss(0.0, sigma) for weight in self.weights])

    def forward(self, inputs: Sequence[float]) -> list[float]:
        """Return the outputs, each between -1 and 1, for ``inputs``."""
        values = list(inputs)
        for neurons in self._layers:
            values = [math.tanh(bias + sum(map(operator.mul, row, values))) for bias, row in neurons]
        return values

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly description of the network."""
        return {"layer_sizes": list(self.layer_sizes), "weights": [round(weight, 6) for weight in self.weights]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NeuralNetwork:
        """Rebuild a network from :meth:`to_dict`'s output."""
        return cls(data["layer_sizes"], data["weights"])
