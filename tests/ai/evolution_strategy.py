# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""An evolution strategy over neural networks, in the style of Salimans et al. (2017)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np

from tests.ai.neural_network import NeuralNetwork

if TYPE_CHECKING:
    import random
    from collections.abc import Sequence


class EvolutionStrategy:
    """Moves one central network along a gradient estimated from noisy copies of it.

    Each generation holds the centre followed by mirrored pairs ``centre ± sigma * noise``, so a population size is
    rounded down to an odd number. Fitness is turned into centred ranks, which ignores its scale and outliers; each
    pair's rank difference weighs its noise into a gradient estimate, which Adam follows with ``learning_rate``, a
    little weight decay keeping the weights small. Unlike a genetic algorithm, every network of the generation
    contributes to the next one.
    """

    BETAS: ClassVar[tuple[float, float]] = (0.9, 0.999)
    EPSILON: ClassVar[float] = 1e-8

    def __init__(
        self,
        population_size: int,
        sigma: float,
        rng: random.Random,
        *,
        learning_rate: float = 0.01,
        weight_decay: float = 0.005,
    ) -> None:
        """Keep ``population_size`` networks around the centre, perturbing it with noise ``sigma``."""
        if population_size < 3:
            msg = "population_size must be at least 3"
            raise ValueError(msg)
        self.pairs = (population_size - 1) // 2
        self.population_size = 1 + 2 * self.pairs
        self.sigma = sigma
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self._noise_rng = np.random.default_rng(rng.getrandbits(64))
        self._rng = rng
        self._layer_sizes: tuple[int, ...] = ()
        self._centre = np.empty(0)
        self._noise = np.empty((0, 0))
        self._moments = (np.empty(0), np.empty(0))
        self._steps = 0

    def seed(self, layer_sizes: Sequence[int], ancestor: NeuralNetwork | None = None) -> list[NeuralNetwork]:
        """Return a first generation around ``ancestor`` if given, around a random network otherwise."""
        centre = ancestor if ancestor is not None else NeuralNetwork.random(layer_sizes, self._rng)
        self._layer_sizes = tuple(layer_sizes)
        self._centre = centre.weights.copy()
        self._moments = (np.zeros_like(self._centre), np.zeros_like(self._centre))
        self._steps = 0
        return self._sample()

    def next_generation(self, population: Sequence[NeuralNetwork], fitness: Sequence[float]) -> list[NeuralNetwork]:
        """Step the centre along the gradient given by ``fitness`` of ``population``, the last generation returned."""
        if len(population) != self.population_size or len(fitness) != self.population_size:
            msg = f"expected the {self.population_size} networks of the last generation"
            raise ValueError(msg)
        perturbed = np.asarray(fitness[1:], dtype=np.float64)
        ranks = perturbed.argsort().argsort() / (len(perturbed) - 1) - 0.5
        gradient = (ranks[0::2] - ranks[1::2]) @ self._noise / (len(perturbed) * self.sigma)
        gradient -= self.weight_decay * self._centre
        self._centre += self._adam(gradient)
        return self._sample()

    def _adam(self, gradient: np.ndarray) -> np.ndarray:
        """Return the Adam step that climbs ``gradient``."""
        (beta1, beta2), (mean, square) = self.BETAS, self._moments
        self._steps += 1
        mean = beta1 * mean + (1 - beta1) * gradient
        square = beta2 * square + (1 - beta2) * gradient**2
        self._moments = (mean, square)
        corrected = self.learning_rate * np.sqrt(1 - beta2**self._steps) / (1 - beta1**self._steps)
        return corrected * mean / (np.sqrt(square) + self.EPSILON)

    def _sample(self) -> list[NeuralNetwork]:
        """Return the centre followed by fresh mirrored pairs of noisy copies of it."""
        self._noise = self._noise_rng.standard_normal((self.pairs, len(self._centre)))
        population = [NeuralNetwork(self._layer_sizes, self._centre.copy())]
        for noise in self._noise:
            population.append(NeuralNetwork(self._layer_sizes, self._centre + self.sigma * noise))
            population.append(NeuralNetwork(self._layer_sizes, self._centre - self.sigma * noise))
        return population
