# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Axis-aligned bounding boxes used for collisions."""

from __future__ import annotations

from dataclasses import dataclass

from synthride.core.vector3 import Vector3


@dataclass(frozen=True)
class BoundingBox:
    """An axis-aligned box defined by its minimum and maximum corners."""

    minimum: Vector3
    maximum: Vector3

    @classmethod
    def from_bottom_center(cls, bottom_center: Vector3, width: float, height: float, length: float) -> BoundingBox:
        """Build a box of the given size standing on ``bottom_center``."""
        half_width, half_length = width / 2, length / 2
        return cls(
            Vector3(bottom_center.x - half_width, bottom_center.y, bottom_center.z - half_length),
            Vector3(bottom_center.x + half_width, bottom_center.y + height, bottom_center.z + half_length),
        )

    @property
    def center_x(self) -> float:
        """The x coordinate of the box's centre."""
        return (self.minimum.x + self.maximum.x) / 2

    def overlap_x(self, other: BoundingBox) -> float:
        """Return how much the two boxes overlap along the x axis."""
        return max(0.0, min(self.maximum.x, other.maximum.x) - max(self.minimum.x, other.minimum.x))

    def overlap_z(self, other: BoundingBox) -> float:
        """Return how much the two boxes overlap along the z axis."""
        return max(0.0, min(self.maximum.z, other.maximum.z) - max(self.minimum.z, other.minimum.z))

    def overlaps_footprint(self, other: BoundingBox) -> bool:
        """Return True when the two boxes overlap when seen from above (x/z plane)."""
        return self.overlap_x(other) > 0 and self.overlap_z(other) > 0
