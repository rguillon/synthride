# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The ship's velocity from input, gravity and the surface underneath."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from synthride.core.game_event import GameEvent
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3

if TYPE_CHECKING:
    from synthride.core.game_config import GameConfig
    from synthride.core.ship import Ship
    from synthride.core.ship_input import ShipInput


class ShipPhysics:
    """Turns player input, gravity and the surface underneath into the ship's velocity for one step.

    On ice the ship only slowly gets the sideways speed the player asks for, so it keeps sliding. Pushers
    add a constant sideways drift. Holding jump on the ground keeps hopping, and a jump off a ramp keeps the
    ramp's climb; once airborne, a fresh press gives one more jump, recharged on landing. That press does
    nothing while the ship already climbs faster than it would, so it never cuts short a jump pad's launch.
    """

    PUSH_DIRECTIONS: ClassVar[dict[TileType, int]] = {TileType.PUSH_LEFT: -1, TileType.PUSH_RIGHT: 1}

    def __init__(self, config: GameConfig) -> None:
        """Use the tunables from ``config``."""
        self._config = config

    def apply(self, ship: Ship, ship_input: ShipInput, gravity: float, dt: float) -> GameEvent | None:
        """Update ``ship.velocity`` and return the jump the ship made during this step, if any."""
        speed = self._forward_speed(ship.speed, ship_input, dt)
        lateral = self._lateral_speed(ship, speed, ship_input, dt)
        vertical = ship.velocity.y
        across, along = ship.ground_slope
        climb = lateral * across + speed * along
        jump = self._jump(ship, ship_input, rising=vertical)
        if jump is GameEvent.JUMPED:
            vertical = self._config.jump_velocity + climb
        elif jump is GameEvent.DOUBLE_JUMPED:
            vertical = self._config.double_jump_velocity
        ship.velocity = Vector3(lateral, vertical - gravity * dt, speed)
        return jump

    def _jump(self, ship: Ship, ship_input: ShipInput, rising: float) -> GameEvent | None:
        fresh_press = ship_input.jump and not ship.jump_held
        ship.jump_held = ship_input.jump
        if ship.grounded:
            ship.air_jump_ready = True
            if ship_input.jump:
                ship.grounded = False
                return GameEvent.JUMPED
        elif fresh_press and ship.air_jump_ready and rising < self._config.double_jump_velocity:
            ship.air_jump_ready = False
            return GameEvent.DOUBLE_JUMPED
        return None

    def _forward_speed(self, speed: float, ship_input: ShipInput, dt: float) -> float:
        config = self._config
        if speed > config.max_speed:
            speed = max(config.max_speed, speed - config.boost_decay * dt)
        elif ship_input.accelerate:
            speed = min(config.max_speed, speed + config.acceleration * dt)
        if ship_input.brake:
            speed -= config.brake_deceleration * dt
        return max(0.0, speed)

    def _lateral_speed(self, ship: Ship, speed: float, ship_input: ShipInput, dt: float) -> float:
        config = self._config
        direction = int(ship_input.right) - int(ship_input.left)
        wanted = direction * max(config.min_strafe_speed, speed * config.strafe_ratio)
        if ship.surface is TileType.ICE:
            current = ship.velocity.x
            return current + (wanted - current) * min(1.0, config.ice_grip * dt)
        return wanted + self.PUSH_DIRECTIONS.get(ship.surface, 0) * config.push_speed
