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

    def add_sloped_box(  # noqa: PLR0913
        self,
        minimum: Vector3,
        maximum: Vector3,
        heights: tuple[float, float, float, float],
        *,
        top_color: Rgb = WHITE,
        wall_upper: Rgb = WHITE,
        wall_lower: Rgb = WHITE,
    ) -> None:
        """Add a box from ``minimum`` up to a slanted top, minus its bottom face; ``maximum.y`` is ignored.

        ``heights`` are the top's heights at the corners (x0, z0), (x1, z0), (x1, z1) and (x0, z1). The top is
        cut into two flat triangles along the diagonal through its highest corner, which follows the crease
        of a corner slope.
        """
        x0, y0, z0 = minimum.x, minimum.y, minimum.z
        x1, z1 = maximum.x, maximum.z
        h00, h10, h11, h01 = heights
        walls = (
            ((x1, y0, z1), (x1, y0, z0), (x1, h10, z0), (x1, h11, z1)),
            ((x0, y0, z0), (x0, y0, z1), (x0, h01, z1), (x0, h00, z0)),
            ((x0, y0, z1), (x1, y0, z1), (x1, h11, z1), (x0, h01, z1)),
            ((x1, y0, z0), (x0, y0, z0), (x0, h00, z0), (x1, h10, z0)),
        )
        for wall in walls:
            self.add_quad(wall, [wall_lower, wall_lower, wall_upper, wall_upper])
        top = [(x0, h01, z1), (x1, h11, z1), (x1, h10, z0), (x0, h00, z0)]
        apex = max(range(4), key=lambda index: top[index][1])
        a, b, c, d = (top[(apex + offset) % 4] for offset in range(4))
        self.add_triangle((a, b, c), top_color)
        self.add_triangle((a, c, d), top_color)
        self.box_count += 1

    def add_quad(self, corners: Sequence[Corner], colors: Sequence[Rgb]) -> None:
        """Add a flat quad, wound counter-clockwise seen from the side it faces. ``colors`` go with ``corners``."""
        a, b, c, d = corners
        normal = self._normal([c[i] - a[i] for i in range(3)], [d[i] - b[i] for i in range(3)])
        for index in (0, 1, 2, 0, 2, 3):
            self.positions.extend(corners[index])
            self.normals.extend(normal)
            self.colors.extend(colors[index])

    def add_triangle(self, corners: Sequence[Corner], color: Rgb) -> None:
        """Add a flat triangle of one colour, wound counter-clockwise seen from the side it faces."""
        a, b, c = corners
        normal = self._normal([b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)])
        for corner in corners:
            self.positions.extend(corner)
            self.normals.extend(normal)
            self.colors.extend(color)

    @staticmethod
    def _normal(u: Sequence[float], v: Sequence[float]) -> tuple[float, ...]:
        normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        length = math.sqrt(sum(component * component for component in normal)) or 1.0
        return tuple(component / length for component in normal)

    @property
    def vertex_count(self) -> int:
        """The number of vertices added so far."""
        return len(self.positions) // 3
