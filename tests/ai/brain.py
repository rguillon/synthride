# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The trained network and its training record."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tests.ai.neural_network import NeuralNetwork


@dataclass(frozen=True)
class Brain:
    """The best network found so far, with the generation that produced it and the fitness it scored."""

    network: NeuralNetwork
    generation: int = 0
    fitness: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly description of the brain."""
        return {"generation": self.generation, "fitness": round(self.fitness, 4), "network": self.network.to_dict()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Brain:
        """Rebuild a brain from :meth:`to_dict`'s output."""
        return cls(NeuralNetwork.from_dict(data["network"]), data["generation"], data["fitness"])
