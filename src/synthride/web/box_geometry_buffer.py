# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Batching of boxes and quads into flat vertex lists."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from synthride.core.vector3 import Vector3

Rgb = tuple[float, float, float]
Corner = tuple[float, float, float]
WHITE: Rgb = (1.0, 1.0, 1.0)


class BoxGeometryBuffer:
    """Accumulates many boxes (and loose quads) into flat vertex lists, so a whole track renders in a few draw calls.

    Faces are wound counter-clockwise seen from outside. The bottom face is skipped: it is never visible.
    Each vertex carries a colour: the top face takes ``top_color`` and the walls fade from ``wall_upper``
    at their top edge to ``wall_lower`` at their foot, which gives the boxes their sense of mass.
    """

    def __init__(self) -> None:
        """Start with empty vertex lists."""
        self.positions: list[float] = []
        self.normals: list[float] = []
        self.colors: list[float] = []
        self.box_count = 0

    def add_box(
        self,
        minimum: Vector3,
        maximum: Vector3,
        top_color: Rgb = WHITE,
        wall_upper: Rgb = WHITE,
        wall_lower: Rgb = WHITE,
    ) -> None:
        """Add the box from ``minimum`` to ``maximum``, minus its bottom face."""
        x0, y0, z0 = minimum.x, minimum.y, minimum.z
        x1, y1, z1 = maximum.x, maximum.y, maximum.z
        faces = (
            ((1, 0, 0), ((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1))),
            ((-1, 0, 0), ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0))),
            ((0, 1, 0), ((x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0))),
            ((0, 0, 1), ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))),
            ((0, 0, -1), ((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0))),
        )
        for normal, (a, b, c, d) in faces:
            for corner in (a, b, c, a, c, d):
                self.positions.extend(corner)
                self.normals.extend(normal)
                if normal[1]:
                    self.colors.extend(top_color)
                else:
                    self.colors.extend(wall_upper if corner[1] == y1 else wall_lower)
        self.box_count += 1

    def add_quad(self, corners: Sequence[Corner], colors: Sequence[Rgb]) -> None:
        """Add a flat quad, wound counter-clockwise seen from the side it faces. ``colors`` go with ``corners``."""
        a, b, c, d = corners
        diagonal, other = [c[i] - a[i] for i in range(3)], [d[i] - b[i] for i in range(3)]
        normal = (
            diagonal[1] * other[2] - diagonal[2] * other[1],
            diagonal[2] * other[0] - diagonal[0] * other[2],
            diagonal[0] * other[1] - diagonal[1] * other[0],
        )
        length = math.sqrt(sum(component * component for component in normal)) or 1.0
        normal = tuple(component / length for component in normal)
        for index in (0, 1, 2, 0, 2, 3):
            self.positions.extend(corners[index])
            self.normals.extend(normal)
            self.colors.extend(colors[index])

    @property
    def vertex_count(self) -> int:
        """The number of vertices added so far."""
        return len(self.positions) // 3
