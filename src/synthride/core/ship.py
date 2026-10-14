# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The player's ship."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from synthride.core.bounding_box import BoundingBox
from synthride.core.vector3 import Vector3

if TYPE_CHECKING:
    from synthride.core.game_config import GameConfig
    from synthride.core.tile_type import TileType


@dataclass
class Ship:
    """The player's ship. ``position`` is the centre of the bottom face of its bounding box.

    ``surface`` is the type of tile the ship rode on during the last step, None while airborne.
    ``air_jump_ready`` is whether the one jump allowed in mid-air is still available; ``jump_held`` is
    whether jump was held during the last step, so a mid-air jump needs a fresh press.
    """

    position: Vector3
    width: float = 0.7
    height: float = 0.3
    length: float = 0.8
    velocity: Vector3 = field(default_factory=Vector3)
    grounded: bool = False
    surface: TileType | None = None
    air_jump_ready: bool = False
    jump_held: bool = False

    @classmethod
    def from_config(cls, position: Vector3, config: GameConfig) -> Ship:
        """Create a ship at ``position`` with the dimensions from ``config``."""
        return cls(position, config.ship_width, config.ship_height, config.ship_length)

    @property
    def speed(self) -> float:
        """The forward speed."""
        return self.velocity.z

    @property
    def bounding_box(self) -> BoundingBox:
        """The ship's box at its current position."""
        return self.box_at(self.position)

    def box_at(self, position: Vector3) -> BoundingBox:
        """Return the ship's box if it stood at ``position``."""
        return BoundingBox.from_bottom_center(position, self.width, self.height, self.length)
