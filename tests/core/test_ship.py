# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.game_config import GameConfig
from synthride.core.ship import Ship
from synthride.core.vector3 import Vector3


def test_from_config_uses_ship_dimensions() -> None:
    config = GameConfig(ship_width=0.5, ship_height=0.2, ship_length=1.0)
    ship = Ship.from_config(Vector3(4, 1, 2), config)
    assert (ship.width, ship.height, ship.length) == (0.5, 0.2, 1.0)


def test_bounding_box_is_centred_on_bottom_position() -> None:
    ship = Ship(Vector3(4, 1, 2), width=0.5, height=0.2, length=1.0)
    assert ship.bounding_box.minimum == Vector3(3.75, 1, 1.5)
    assert ship.bounding_box.maximum == Vector3(4.25, 1.2, 2.5)


def test_speed_is_forward_velocity() -> None:
    ship = Ship(Vector3(), velocity=Vector3(1, 2, 3))
    assert ship.speed == 3
