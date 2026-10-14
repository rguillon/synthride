import pytest

from synthride.core.collision_outcome import CollisionOutcome
from synthride.core.collision_resolver import CollisionResolver
from synthride.core.game_config import GameConfig
from synthride.core.level_parser import LevelParser
from synthride.core.ship import Ship
from synthride.core.track import Track
from synthride.core.vector3 import Vector3

CONFIG = GameConfig()
FLAT = "N1 N1 N1 N1 N1 N1 N1 N1"


def make_track(*rows: str) -> Track:
    return LevelParser().parse("---\n" + "\n".join(rows)).track


def make_ship(x=4.5, y=0.5, z=0.5, velocity: Vector3 | None = None, width=CONFIG.ship_width) -> Ship:
    return Ship(Vector3(x, y, z), width=width, velocity=velocity or Vector3(), grounded=True)


def outcomes(reports):
    return [report.outcome for report in reports]


def test_lands_on_tile_top():
    ship = make_ship(y=0.55, velocity=Vector3(0, -5, 0))
    reports = CollisionResolver(make_track(FLAT), CONFIG).move(ship, 0.02)
    assert outcomes(reports) == [CollisionOutcome.LANDED]
    assert reports[0].tile is not None
    assert reports[0].tile.column == 4
    assert ship.position.y == 0.5
    assert ship.velocity.y == 0
    assert ship.grounded


def test_flies_when_above_surface():
    ship = make_ship(y=2, velocity=Vector3(0, -1, 0))
    assert CollisionResolver(make_track(FLAT), CONFIG).move(ship, 0.02) == []
    assert not ship.grounded
    assert ship.position.y == pytest.approx(1.98)


def test_full_frontal_hit_crashes():
    track = make_track(FLAT, "N2 N2 N2 N2 N2 N2 N2 N2")
    ship = make_ship(velocity=Vector3(0, 0, 10))
    reports = CollisionResolver(track, CONFIG).move(ship, 0.02)
    assert outcomes(reports) == [CollisionOutcome.CRASHED]
    assert ship.velocity.z == 0
    assert ship.bounding_box.maximum.z <= 1


@pytest.mark.parametrize(
    ("row", "x", "expected_x"),
    [
        ("N1 N1 N1 N1 N1 N2 N1 N1", 4.75, 5 - CONFIG.ship_width / 2),
        ("N1 N1 N1 N2 N1 N1 N1 N1", 4.25, 4 + CONFIG.ship_width / 2),
    ],
)
def test_corner_hit_nudges_ship_sideways(row, x, expected_x):
    ship = make_ship(x=x, velocity=Vector3(0, 0, 10))
    reports = CollisionResolver(make_track(FLAT, row), CONFIG).move(ship, 0.02)
    assert CollisionOutcome.NUDGED in outcomes(reports)
    assert ship.position.x == pytest.approx(expected_x, abs=1e-4)
    assert ship.position.z == pytest.approx(0.7)
    assert ship.velocity.z == 10


def test_corner_hit_without_room_crashes():
    track = make_track(FLAT, "N1 N1 N1 N2 .. N2 N1 N1")
    ship = make_ship(x=4.5, width=1.05, velocity=Vector3(0, 0, 10))
    assert outcomes(CollisionResolver(track, CONFIG).move(ship, 0.02)) == [CollisionOutcome.CRASHED]


def test_lower_tile_ahead_does_not_block():
    track = make_track("N2 N2 N2 N2 N2 N2 N2 N2", FLAT)
    ship = make_ship(y=1.0, velocity=Vector3(0, -0.1, 10))
    assert CollisionOutcome.CRASHED not in outcomes(CollisionResolver(track, CONFIG).move(ship, 0.02))


def test_side_wall_stops_strafing():
    track = make_track("N1 N1 N1 N1 N1 N2 N1 N1")
    ship = make_ship(velocity=Vector3(5, 0, 0))
    CollisionResolver(track, CONFIG).move(ship, 0.1)
    assert ship.position.x == pytest.approx(5 - CONFIG.ship_width / 2, abs=1e-4)
    assert ship.velocity.x == 0


def test_strafing_left_into_wall():
    track = make_track("N1 N1 N1 N2 N1 N1 N1 N1")
    ship = make_ship(velocity=Vector3(-5, 0, 0))
    CollisionResolver(track, CONFIG).move(ship, 0.1)
    assert ship.position.x == pytest.approx(4 + CONFIG.ship_width / 2, abs=1e-4)


def test_falls_off_below_limit():
    ship = make_ship(y=CONFIG.fall_limit_y + 0.1, velocity=Vector3(0, -10, 0))
    track = make_track(".. .. .. .. .. .. .. ..")
    assert outcomes(CollisionResolver(track, CONFIG).move(ship, 0.02)) == [CollisionOutcome.FELL]
