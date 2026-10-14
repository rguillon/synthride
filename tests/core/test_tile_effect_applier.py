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


def apply(tile_type: TileType, speed: float = 10.0, fuel: Gauge | None = None):
    ship = Ship(Vector3(), velocity=Vector3(0, 0, speed))
    event = TileEffectApplier(CONFIG).apply(Tile(tile_type, 0, 0, 1), ship, fuel or Gauge(10))
    return event, ship


def test_normal_tile_does_nothing():
    assert apply(TileType.NORMAL) == (None, Ship(Vector3(), velocity=Vector3(0, 0, 10)))


def test_boost_sets_overspeed_once():
    event, ship = apply(TileType.BOOST)
    assert event is GameEvent.BOOSTED
    assert ship.speed == pytest.approx(CONFIG.max_speed * CONFIG.boost_factor)
    event, ship = apply(TileType.BOOST, speed=CONFIG.max_speed + 0.1)
    assert event is None
    assert ship.speed == pytest.approx(CONFIG.max_speed * CONFIG.boost_factor)
    assert apply(TileType.BOOST, speed=100)[0] is None


def test_slow_caps_speed():
    event, ship = apply(TileType.SLOW, speed=CONFIG.max_speed)
    assert event is GameEvent.SLOWED
    assert ship.speed == pytest.approx(CONFIG.max_speed * CONFIG.slow_factor)
    assert apply(TileType.SLOW, speed=1)[0] is None


def test_kill_burns():
    assert apply(TileType.KILL)[0] is GameEvent.BURNED


def test_refuel_only_when_not_full():
    fuel = Gauge(10)
    assert apply(TileType.REFUEL, fuel=fuel)[0] is None
    fuel.drain(5)
    assert apply(TileType.REFUEL, fuel=fuel)[0] is GameEvent.REFUELED
    assert fuel.is_full


def test_finish_wins():
    assert apply(TileType.FINISH)[0] is GameEvent.LEVEL_WON
