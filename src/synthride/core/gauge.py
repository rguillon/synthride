# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Drainable and refillable resources."""


class Gauge:
    """A resource that drains over time and can be refilled, such as fuel or oxygen."""

    def __init__(self, capacity: float) -> None:
        """Create a full gauge holding up to ``capacity``."""
        if capacity <= 0:
            msg = "capacity must be positive"
            raise ValueError(msg)
        self.capacity = capacity
        self.value = capacity

    @property
    def fraction(self) -> float:
        """The remaining fraction of the capacity, from 0 to 1."""
        return self.value / self.capacity

    @property
    def is_empty(self) -> bool:
        """Whether nothing is left."""
        return self.value <= 0

    @property
    def is_full(self) -> bool:
        """Whether the gauge is at capacity."""
        return self.value >= self.capacity

    def drain(self, amount: float) -> None:
        """Remove ``amount``, never going below zero."""
        self.value = max(0.0, self.value - amount)

    def refill(self) -> None:
        """Fill the gauge back to capacity."""
        self.value = self.capacity
