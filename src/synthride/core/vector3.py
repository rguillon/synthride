from __future__ import annotations

import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Vector3:
    """An immutable 3D vector. x is lateral, y is up, z is forward along the track."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: Vector3) -> Vector3:
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3) -> Vector3:
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vector3:
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def with_x(self, x: float) -> Vector3:
        return replace(self, x=x)

    def with_y(self, y: float) -> Vector3:
        return replace(self, y=y)

    def with_z(self, z: float) -> Vector3:
        return replace(self, z=z)
