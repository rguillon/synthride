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
    """A box the ship collides with: a tile's block, or a piece of a tunnel's shell (with no tile)."""

    box: BoundingBox
    tile: Tile | None = None
