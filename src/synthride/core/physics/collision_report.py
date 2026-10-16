# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""A collision outcome paired with the tile that caused it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synthride.core.physics.collision_outcome import CollisionOutcome
    from synthride.core.world.tile import Tile


@dataclass(frozen=True)
class CollisionReport:
    """A collision outcome together with the tile involved, if any."""

    outcome: CollisionOutcome
    tile: Tile | None = None
