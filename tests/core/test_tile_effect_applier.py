# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.game_config import GameConfig
from synthride.core.game_event import GameEvent
from synthride.core.gauge import Gauge
from synthride.core.ship import Ship
from synthride.core.tile import Tile
from synthride.core.tile_effect_applier import TileEffectApplier
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3

CONFIG = GameConfig()


def apply(
    tile_type: TileType,
    speed: float = 10.0,
    fuel: Gauge | None = None,
    oxygen: Gauge | None = None,
    surface: TileType | None = None,
) -> tuple[GameEvent | None, Ship]:
    ship = Ship(Vector3(), velocity=Vector3(0, 0, speed), grounded=True, surface=surface)
    event = TileEffectApplier(CONFIG).apply(Tile(tile_type, 0, 0, 1), ship, fuel or Gauge(10), oxygen or Gauge(10))
    return event, ship


def test_normal_tile_does_nothing() -> None:
    assert apply(TileType.NORMAL) == (None, Ship(Vector3(), velocity=Vector3(0, 0, 10), grounded=True))


def test_boost_sets_overspeed_once() -> None:
    event, ship = apply(TileType.BOOST)
    assert event is GameEvent.BOOSTED
    assert ship.speed == pytest.approx(CONFIG.max_speed * CONFIG.boost_factor)
    event, ship = apply(TileType.BOOST, speed=CONFIG.max_speed + 0.1)
    assert event is None
    assert ship.speed == pytest.approx(CONFIG.max_speed * CONFIG.boost_factor)
    assert apply(TileType.BOOST, speed=100)[0] is None


def test_slow_caps_speed() -> None:
    event, ship = apply(TileType.SLOW, speed=CONFIG.max_speed)
    assert event is GameEvent.SLOWED
    assert ship.speed == pytest.approx(CONFIG.max_speed * CONFIG.slow_factor)
    assert apply(TileType.SLOW, speed=1)[0] is None


def test_kill_burns() -> None:
    assert apply(TileType.KILL)[0] is GameEvent.BURNED


def test_refuel_only_when_not_full() -> None:
    fuel = Gauge(10)
    assert apply(TileType.REFUEL, fuel=fuel)[0] is None
    fuel.drain(5)
    assert apply(TileType.REFUEL, fuel=fuel)[0] is GameEvent.REFUELED
    assert fuel.is_full


def test_finish_wins() -> None:
    assert apply(TileType.FINISH)[0] is GameEvent.LEVEL_WON


def test_air_refills_oxygen_only_when_not_full() -> None:
    oxygen = Gauge(10)
    assert apply(TileType.AIR, oxygen=oxygen)[0] is None
    oxygen.drain(5)
    assert apply(TileType.AIR, oxygen=oxygen)[0] is GameEvent.REFILLED_AIR
    assert oxygen.is_full


def test_jump_pad_launches_the_ship() -> None:
    event, ship = apply(TileType.JUMP)
    assert event is GameEvent.LAUNCHED
    assert ship.velocity.y == CONFIG.launch_velocity
    assert not ship.grounded


@pytest.mark.parametrize(
    ("tile_type", "expected"),
    [
        (TileType.ICE, GameEvent.SKIDDED),
        (TileType.PUSH_LEFT, GameEvent.PUSHED),
        (TileType.PUSH_RIGHT, GameEvent.PUSHED),
    ],
)
def test_lasting_effects_report_only_when_getting_on(tile_type: TileType, expected: GameEvent) -> None:
    assert apply(tile_type, surface=TileType.NORMAL)[0] is expected
    assert apply(tile_type, surface=None)[0] is expected
    assert apply(tile_type, surface=tile_type)[0] is None


@pytest.mark.parametrize(
    ("tile_type", "event"), [(TileType.REFUEL, GameEvent.REFUELED), (TileType.AIR, GameEvent.REFILLED_AIR)]
)
def test_refills_keep_working_but_report_once_per_patch(tile_type: TileType, event: GameEvent) -> None:
    fuel, oxygen = Gauge(10), Gauge(10)
    fuel.drain(5)
    oxygen.drain(5)
    assert apply(tile_type, fuel=fuel, oxygen=oxygen, surface=tile_type)[0] is None
    assert (fuel if tile_type is TileType.REFUEL else oxygen).is_full
    fuel.drain(5)
    oxygen.drain(5)
    assert apply(tile_type, fuel=fuel, oxygen=oxygen, surface=TileType.NORMAL)[0] is event


def test_slow_keeps_capping_but_reports_once_per_patch() -> None:
    event, ship = apply(TileType.SLOW, speed=CONFIG.max_speed, surface=TileType.SLOW)
    assert event is None
    assert ship.speed == pytest.approx(CONFIG.max_speed * CONFIG.slow_factor)
