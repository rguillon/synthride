import pytest

from synthride.core.game_config import GameConfig
from synthride.core.ship import Ship
from synthride.core.ship_input import ShipInput
from synthride.core.ship_physics import ShipPhysics
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3

CONFIG = GameConfig()


def make_ship(speed: float = 0.0, grounded: bool = True) -> Ship:
    return Ship(Vector3(4, 0.5, 1), velocity=Vector3(0, 0, speed), grounded=grounded)


def test_accelerates_up_to_max_speed():
    ship = make_ship(speed=CONFIG.max_speed - 0.01)
    ShipPhysics(CONFIG).apply(ship, ShipInput(accelerate=True), gravity=0, dt=1)
    assert ship.speed == CONFIG.max_speed


def test_keeps_speed_without_input():
    ship = make_ship(speed=5)
    ShipPhysics(CONFIG).apply(ship, ShipInput(), gravity=0, dt=0.1)
    assert ship.speed == 5


def test_brakes_but_never_reverses():
    ship = make_ship(speed=1)
    ShipPhysics(CONFIG).apply(ship, ShipInput(brake=True), gravity=0, dt=1)
    assert ship.speed == 0


def test_overspeed_decays_toward_max():
    ship = make_ship(speed=CONFIG.max_speed + 1)
    ShipPhysics(CONFIG).apply(ship, ShipInput(accelerate=True), gravity=0, dt=0.1)
    assert CONFIG.max_speed < ship.speed < CONFIG.max_speed + 1


@pytest.mark.parametrize(("ship_input", "sign"), [(ShipInput(left=True), -1), (ShipInput(right=True), 1)])
def test_strafes_with_minimum_speed(ship_input, sign):
    ship = make_ship(speed=0)
    ShipPhysics(CONFIG).apply(ship, ship_input, gravity=0, dt=0.1)
    assert ship.velocity.x == sign * CONFIG.min_strafe_speed


def test_strafe_scales_with_speed():
    ship = make_ship(speed=CONFIG.max_speed)
    ShipPhysics(CONFIG).apply(ship, ShipInput(right=True), gravity=0, dt=0.01)
    assert ship.velocity.x == pytest.approx(CONFIG.max_speed * CONFIG.strafe_ratio)


def test_jumps_only_when_grounded():
    physics = ShipPhysics(CONFIG)
    ship = make_ship()
    assert physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01)
    assert ship.velocity.y == pytest.approx(CONFIG.jump_velocity - 0.1)
    assert not ship.grounded
    assert not physics.apply(ship, ShipInput(jump=True), gravity=10, dt=0.01)


def test_gravity_pulls_down():
    ship = make_ship(grounded=False)
    ShipPhysics(CONFIG).apply(ship, ShipInput(), gravity=10, dt=0.5)
    assert ship.velocity.y == -5


def test_ice_keeps_the_ship_sliding_sideways():
    ship = make_ship(speed=10)
    ship.surface = TileType.ICE
    ship.velocity = ship.velocity.with_x(3.0)
    ShipPhysics(CONFIG).apply(ship, ShipInput(), gravity=0, dt=0.1)
    assert 0 < ship.velocity.x < 3.0
    ship.velocity = ship.velocity.with_x(0.0)
    ShipPhysics(CONFIG).apply(ship, ShipInput(right=True), gravity=0, dt=0.1)
    assert 0 < ship.velocity.x < CONFIG.min_strafe_speed


@pytest.mark.parametrize(("surface", "direction"), [(TileType.PUSH_LEFT, -1), (TileType.PUSH_RIGHT, 1)])
def test_pushers_drift_the_ship_sideways(surface, direction):
    ship = make_ship(speed=10)
    ship.surface = surface
    ShipPhysics(CONFIG).apply(ship, ShipInput(), gravity=0, dt=0.1)
    assert ship.velocity.x == direction * CONFIG.push_speed
