from __future__ import annotations

from dataclasses import dataclass

from synthride.core.collision_outcome import CollisionOutcome
from synthride.core.tile import Tile


@dataclass(frozen=True)
class CollisionReport:
    """A collision outcome together with the tile involved, if any."""

    outcome: CollisionOutcome
    tile: Tile | None = None
