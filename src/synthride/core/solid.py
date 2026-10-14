# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Boxes the ship collides with."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synthride.core.bounding_box import BoundingBox
    from synthride.core.tile import Tile


@dataclass(frozen=True)
class Solid:
    """A box the ship collides with: a tile's block, or a piece of a tunnel's shell (with no tile).

    An oblique tile's box reaches up to its raised side, but its real top is the slope underneath the ship.
    """

    box: BoundingBox
    tile: Tile | None = None

    def top_over(self, box: BoundingBox) -> float:
        """Return the height of the solid's top under the footprint of ``box``."""
        if self.tile is None or self.tile.slope is None:
            return self.box.maximum.y
        return self.tile.top_over(box)
