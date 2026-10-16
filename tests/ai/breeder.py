# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""What the trainer needs from an optimiser."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tests.ai.neural_network import NeuralNetwork


class Breeder(Protocol):
    """Proposes generations of networks and learns from how each one scored."""

    def seed(self, layer_sizes: Sequence[int], ancestor: NeuralNetwork | None = None) -> list[NeuralNetwork]:
        """Return a first generation, built around ``ancestor`` if given, random otherwise."""
        ...

    def next_generation(self, population: Sequence[NeuralNetwork], fitness: Sequence[float]) -> list[NeuralNetwork]:
        """Return the generation that follows ``population``, scored by ``fitness``."""
        ...
