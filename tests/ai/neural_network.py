# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""A small fully connected neural network computed with NumPy."""

from __future__ import annotations

import itertools
import math
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence
    from random import Random


class NeuralNetwork:
    """A multilayer perceptron with tanh activations, its weights kept in one flat array.

    Each layer stores, for every output neuron, its bias followed by one weight per input.
    """

    def __init__(self, layer_sizes: Sequence[int], weights: Sequence[float] | np.ndarray) -> None:
        """Build a network with ``layer_sizes`` neurons per layer (inputs first) from its flat ``weights``."""
        self.layer_sizes = tuple(layer_sizes)
        if len(self.layer_sizes) < 2:
            msg = "a network needs at least an input and an output layer"
            raise ValueError(msg)
        if len(weights) != self.weight_count(self.layer_sizes):
            msg = f"expected {self.weight_count(self.layer_sizes)} weights, got {len(weights)}"
            raise ValueError(msg)
        self.weights = np.asarray(weights, dtype=np.float64)
        self._layers: list[tuple[np.ndarray, np.ndarray]] = []
        start = 0
        for inputs, outputs in itertools.pairwise(self.layer_sizes):
            block = self.weights[start : start + (inputs + 1) * outputs].reshape(outputs, inputs + 1)
            self._layers.append((block[:, 1:], block[:, 0]))
            start += (inputs + 1) * outputs

    @staticmethod
    def weight_count(layer_sizes: Sequence[int]) -> int:
        """Return the number of weights, biases included, of a network with ``layer_sizes``."""
        return sum((inputs + 1) * outputs for inputs, outputs in itertools.pairwise(layer_sizes))

    @classmethod
    def random(cls, layer_sizes: Sequence[int], rng: Random) -> NeuralNetwork:
        """Create a network with small random weights scaled to each layer's fan-in, and zero biases."""
        noise = np.random.default_rng(rng.getrandbits(64))
        blocks = []
        for inputs, outputs in itertools.pairwise(layer_sizes):
            block = noise.normal(0.0, 1 / math.sqrt(inputs), (outputs, inputs + 1))
            block[:, 0] = 0.0
            blocks.append(block.ravel())
        return cls(layer_sizes, np.concatenate(blocks))

    def mutated(self, sigma: float, rng: Random) -> NeuralNetwork:
        """Return a copy with gaussian noise of standard deviation ``sigma`` added to every weight."""
        noise = np.random.default_rng(rng.getrandbits(64))
        return NeuralNetwork(self.layer_sizes, self.weights + noise.normal(0.0, sigma, self.weights.shape))

    def forward(self, inputs: Sequence[float] | np.ndarray) -> list[float]:
        """Return the outputs, each between -1 and 1, for ``inputs``."""
        values = np.asarray(inputs, dtype=np.float64)
        for weights, biases in self._layers:
            values = np.tanh(weights @ values + biases)
        return values.tolist()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly description of the network."""
        return {"layer_sizes": list(self.layer_sizes), "weights": np.round(self.weights, 6).tolist()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NeuralNetwork:
        """Rebuild a network from :meth:`to_dict`'s output."""
        return cls(data["layer_sizes"], data["weights"])
