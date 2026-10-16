# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.game_config import GameConfig
from synthride.core.game_event import GameEvent
from synthride.core.ship import Ship
from synthride.core.ship_input import ShipInput
from synthride.core.ship_physics import ShipPhysics
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3

CONFIG = GameConfig()


def make_ship(speed: float = 0.0, *, grounded: bool = True) -> Ship:
    return Ship(Vector3(4, 0.5, 1), velocity=Vector3(0, 0, speed), grounded=grounded)


def test_accelerates_up_to_max_speed() -> None:
    ship = make_ship(speed=CONFIG.max_speed - 0.01)
    ShipPhysics(CONFIG).apply(ship, ShipInput(accelerate=True), gravity=0, dt=1)
    assert ship.speed == CONFIG.max_speed


def test_keeps_speed_without_input() -> None:
    ship = make_ship(speed=5)
    ShipPhysics(CONFIG).apply(ship, ShipInput(), gravity=0, dt=0.1)
    assert ship.speed == 5


def test_brakes_but_never_reverses() -> None:
    ship = make_ship(speed=1)
    ShipPhysics(CONFIG).apply(ship, ShipInput(brake=True), gravity=0, dt=1)
    assert ship.speed == 0


def test_overspeed_decays_toward_max() -> None:
    ship = make_ship(speed=CONFIG.max_speed + 1)
    ShipPhysics(CONFIG).apply(ship, ShipInput(accelerate=True), gravity=0, dt=0.1)
    assert CONFIG.max_speed < ship.speed < CONFIG.max_speed + 1


@pytest.mark.parametrize(("ship_input", "sign"), [(ShipInput(left=True), -1), (ShipInput(right=True), 1)])
def test_strafes_with_minimum_speed(ship_input: ShipInput, sign: int) -> None:
    ship = make_ship(speed=0)
    ShipPhysics(CONFIG).apply(ship, ship_input, gravity=0, dt=0.1)
    assert ship.velocity.x == sign * CONFIG.min_strafe_speed


def test_strafe_scales_with_speed() -> None:
    ship = make_ship(speed=CONFIG.max_speed)
    ShipPhysics(CONFIG).apply(ship, ShipInput(right=True), gravity=0, dt=0.01)
    assert ship.velocity.x == pytest.approx(CONFIG.max_speed * CONFIG.strafe_ratio)


def test_jumps_only_when_grounded() -> None:
    physics = ShipPhysics(CONFIG)
    ship = make_ship()
    assert physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01) is GameEvent.JUMPED
    assert ship.velocity.y == pytest.approx(CONFIG.jump_velocity - 0.1)
    assert not ship.grounded
    assert physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01) is None


def test_jumping_on_a_ramp_keeps_its_climb() -> None:
    ship = make_ship(speed=CONFIG.max_speed)
    ship.ground_slope = (0.0, 0.25)
    ShipPhysics(CONFIG).apply(ship, ShipInput(jump=True), gravity=0, dt=0.01)
    assert ship.velocity.y == pytest.approx(CONFIG.jump_velocity + CONFIG.max_speed * 0.25)


def test_a_fresh_press_in_mid_air_jumps_once_more() -> None:
    physics = ShipPhysics(CONFIG)
    ship = make_ship()
    physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01)
    physics.apply(ship, ShipInput(), gravity=10, dt=0.1)  # slows below a double jump's climb
    assert physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01) is GameEvent.DOUBLE_JUMPED
    assert ship.velocity.y == pytest.approx(CONFIG.double_jump_velocity - 0.1)
    physics.apply(ship, ShipInput(), gravity=10, dt=0.01)
    assert physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01) is None


def test_landing_recharges_the_double_jump() -> None:
    physics = ShipPhysics(CONFIG)
    ship = make_ship()
    physics.apply(ship, ShipInput(), gravity=10, dt=0.01)
    ship.grounded = False
    assert physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01) is GameEvent.DOUBLE_JUMPED
    ship.grounded = True
    physics.apply(ship, ShipInput(), gravity=10, dt=0.01)
    ship.grounded = False
    assert physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01) is GameEvent.DOUBLE_JUMPED


def test_gravity_pulls_down() -> None:
    ship = make_ship(grounded=False)
    ShipPhysics(CONFIG).apply(ship, ShipInput(), gravity=10, dt=0.5)
    assert ship.velocity.y == -5


def test_ice_keeps_the_ship_sliding_sideways() -> None:
    ship = make_ship(speed=10)
    ship.surface = TileType.ICE
    ship.velocity = ship.velocity.with_x(3.0)
    ShipPhysics(CONFIG).apply(ship, ShipInput(), gravity=0, dt=0.1)
    assert 0 < ship.velocity.x < 3.0
    ship.velocity = ship.velocity.with_x(0.0)
    ShipPhysics(CONFIG).apply(ship, ShipInput(right=True), gravity=0, dt=0.1)
    assert 0 < ship.velocity.x < CONFIG.min_strafe_speed


@pytest.mark.parametrize(("surface", "direction"), [(TileType.PUSH_LEFT, -1), (TileType.PUSH_RIGHT, 1)])
def test_pushers_drift_the_ship_sideways(surface: TileType, direction: int) -> None:
    ship = make_ship(speed=10)
    ship.surface = surface
    ShipPhysics(CONFIG).apply(ship, ShipInput(), gravity=0, dt=0.1)
    assert ship.velocity.x == direction * CONFIG.push_speed


def test_a_mid_air_press_never_slows_a_faster_climb() -> None:
    physics = ShipPhysics(CONFIG)
    ship = make_ship()
    physics.apply(ship, ShipInput(), gravity=10, dt=0.01)
    ship.grounded = False
    ship.velocity = ship.velocity.with_y(CONFIG.launch_velocity)  # just thrown up by a jump pad
    assert physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01) is None
    assert ship.velocity.y == pytest.approx(CONFIG.launch_velocity - 0.1)
    ship.velocity = ship.velocity.with_y(0.0)  # at the top of the arc, the double jump is still there
    physics.apply(ship, ShipInput(), gravity=10, dt=0.01)
    assert physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01) is GameEvent.DOUBLE_JUMPED
