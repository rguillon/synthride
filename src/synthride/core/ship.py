from __future__ import annotations

from dataclasses import dataclass, field

from synthride.core.bounding_box import BoundingBox
from synthride.core.game_config import GameConfig
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3


@dataclass
class Ship:
    """The player's ship. ``position`` is the centre of the bottom face of its bounding box.

    ``surface`` is the type of tile the ship rode on during the last step, None while airborne.
    """

    position: Vector3
    width: float = 0.7
    height: float = 0.3
    length: float = 0.8
    velocity: Vector3 = field(default_factory=Vector3)
    grounded: bool = False
    surface: TileType | None = None

    @classmethod
    def from_config(cls, position: Vector3, config: GameConfig) -> Ship:
        return cls(position, config.ship_width, config.ship_height, config.ship_length)

    @property
    def speed(self) -> float:
        return self.velocity.z

    @property
    def bounding_box(self) -> BoundingBox:
        return self.box_at(self.position)

    def box_at(self, position: Vector3) -> BoundingBox:
        return BoundingBox.from_bottom_center(position, self.width, self.height, self.length)
