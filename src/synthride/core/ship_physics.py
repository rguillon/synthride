from __future__ import annotations

from synthride.core.game_config import GameConfig
from synthride.core.ship import Ship
from synthride.core.ship_input import ShipInput
from synthride.core.vector3 import Vector3


class ShipPhysics:
    """Turns player input and gravity into the ship's velocity for one step."""

    def __init__(self, config: GameConfig) -> None:
        self._config = config

    def apply(self, ship: Ship, ship_input: ShipInput, gravity: float, dt: float) -> bool:
        """Updates ``ship.velocity``. Returns True when the ship jumped during this step."""
        speed = self._forward_speed(ship.speed, ship_input, dt)
        lateral = self._lateral_speed(speed, ship_input)
        vertical = ship.velocity.y
        jumped = ship_input.jump and ship.grounded
        if jumped:
            vertical = self._config.jump_velocity
            ship.grounded = False
        ship.velocity = Vector3(lateral, vertical - gravity * dt, speed)
        return jumped

    def _forward_speed(self, speed: float, ship_input: ShipInput, dt: float) -> float:
        config = self._config
        if speed > config.max_speed:
            speed = max(config.max_speed, speed - config.boost_decay * dt)
        elif ship_input.accelerate:
            speed = min(config.max_speed, speed + config.acceleration * dt)
        if ship_input.brake:
            speed -= config.brake_deceleration * dt
        return max(0.0, speed)

    def _lateral_speed(self, speed: float, ship_input: ShipInput) -> float:
        direction = int(ship_input.right) - int(ship_input.left)
        return direction * max(self._config.min_strafe_speed, speed * self._config.strafe_ratio)
