class Gauge:
    """A resource that drains over time and can be refilled, such as fuel or oxygen."""

    def __init__(self, capacity: float) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")  # noqa: TRY003
        self.capacity = capacity
        self.value = capacity

    @property
    def fraction(self) -> float:
        return self.value / self.capacity

    @property
    def is_empty(self) -> bool:
        return self.value <= 0

    @property
    def is_full(self) -> bool:
        return self.value >= self.capacity

    def drain(self, amount: float) -> None:
        self.value = max(0.0, self.value - amount)

    def refill(self) -> None:
        self.value = self.capacity
