# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""A genetic algorithm over neural networks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.ai.neural_network import NeuralNetwork

if TYPE_CHECKING:
    import random
    from collections.abc import Sequence


class Evolution:
    """Breeds generations of networks: the best ``elite_count`` survive unchanged, mutated copies fill the rest."""

    def __init__(self, population_size: int, elite_count: int, sigma: float, rng: random.Random) -> None:
        """Keep ``population_size`` networks, ``elite_count`` of them elites, mutating with noise ``sigma``."""
        if not 0 < elite_count < population_size:
            msg = "elite_count must be between 1 and population_size - 1"
            raise ValueError(msg)
        self.population_size = population_size
        self.elite_count = elite_count
        self.sigma = sigma
        self._rng = rng

    def seed(self, layer_sizes: Sequence[int], ancestor: NeuralNetwork | None = None) -> list[NeuralNetwork]:
        """Return a first generation: ``ancestor`` and its mutants if given, random networks otherwise."""
        if ancestor is None:
            return [NeuralNetwork.random(layer_sizes, self._rng) for _ in range(self.population_size)]
        return self._breed([ancestor])

    def next_generation(self, population: Sequence[NeuralNetwork], fitness: Sequence[float]) -> list[NeuralNetwork]:
        """Return the generation bred from ``population``, scored by ``fitness``, the best first."""
        ranked = sorted(range(len(population)), key=lambda index: fitness[index], reverse=True)
        return self._breed([population[index] for index in ranked[: self.elite_count]])

    def _breed(self, parents: Sequence[NeuralNetwork]) -> list[NeuralNetwork]:
        children = [
            self._rng.choice(parents).mutated(self.sigma, self._rng) for _ in range(self.population_size - len(parents))
        ]
        return [*parents, *children]
