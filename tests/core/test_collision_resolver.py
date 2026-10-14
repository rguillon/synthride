# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.bounding_box import BoundingBox
from synthride.core.collision_outcome import CollisionOutcome
from synthride.core.collision_report import CollisionReport
from synthride.core.collision_resolver import CollisionResolver
from synthride.core.game_config import GameConfig
from synthride.core.level_parser import LevelParser
from synthride.core.ship import Ship
from synthride.core.solid import Solid
from synthride.core.track import Track
from synthride.core.tunnel_span import TunnelSpan
from synthride.core.vector3 import Vector3
from tests.level_json import level_json

CONFIG = GameConfig()
FLAT = "N1 N1 N1 N1 N1 N1 N1 N1"


def make_track(*rows: str) -> Track:
    return LevelParser().parse(level_json(*rows)).track


def make_ship(
    x: float = 4.5, y: float = 0.5, z: float = 0.5, velocity: Vector3 | None = None, width: float = CONFIG.ship_width
) -> Ship:
    return Ship(Vector3(x, y, z), width=width, velocity=velocity or Vector3(), grounded=True)


def outcomes(reports: list[CollisionReport]) -> list[CollisionOutcome]:
    return [report.outcome for report in reports]


def test_lands_on_tile_top() -> None:
    ship = make_ship(y=0.55, velocity=Vector3(0, -5, 0))
    reports = CollisionResolver(make_track(FLAT), CONFIG).move(ship, 0.02)
    assert outcomes(reports) == [CollisionOutcome.LANDED]
    assert reports[0].tile is not None
    assert reports[0].tile.column == 4
    assert ship.position.y == 0.5
    assert ship.velocity.y == 0
    assert ship.grounded


def test_flies_when_above_surface() -> None:
    ship = make_ship(y=2, velocity=Vector3(0, -1, 0))
    assert CollisionResolver(make_track(FLAT), CONFIG).move(ship, 0.02) == []
    assert not ship.grounded
    assert ship.position.y == pytest.approx(1.98)


def test_full_frontal_hit_crashes() -> None:
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
def test_corner_hit_nudges_ship_sideways(row: str, x: float, expected_x: float) -> None:
    ship = make_ship(x=x, velocity=Vector3(0, 0, 10))
    reports = CollisionResolver(make_track(FLAT, row), CONFIG).move(ship, 0.02)
    assert CollisionOutcome.NUDGED in outcomes(reports)
    assert ship.position.x == pytest.approx(expected_x, abs=1e-4)
    assert ship.position.z == pytest.approx(0.7)
    assert ship.velocity.z == 10


def test_corner_hit_without_room_crashes() -> None:
    track = make_track(FLAT, "N1 N1 N1 N2 .. N2 N1 N1")
    ship = make_ship(x=4.5, width=1.05, velocity=Vector3(0, 0, 10))
    assert outcomes(CollisionResolver(track, CONFIG).move(ship, 0.02)) == [CollisionOutcome.CRASHED]


def test_lower_tile_ahead_does_not_block() -> None:
    track = make_track("N2 N2 N2 N2 N2 N2 N2 N2", FLAT)
    ship = make_ship(y=1.0, velocity=Vector3(0, -0.1, 10))
    assert CollisionOutcome.CRASHED not in outcomes(CollisionResolver(track, CONFIG).move(ship, 0.02))


def test_side_wall_stops_strafing() -> None:
    track = make_track("N1 N1 N1 N1 N1 N2 N1 N1")
    ship = make_ship(velocity=Vector3(5, 0, 0))
    reports = CollisionResolver(track, CONFIG).move(ship, 0.1)
    assert ship.position.x == pytest.approx(5 - CONFIG.ship_width / 2, abs=1e-4)
    assert ship.velocity.x == 0
    assert outcomes(reports) == [CollisionOutcome.SCRAPED_RIGHT, CollisionOutcome.LANDED]


def test_strafing_left_into_wall() -> None:
    track = make_track("N1 N1 N1 N2 N1 N1 N1 N1")
    ship = make_ship(velocity=Vector3(-5, 0, 0))
    reports = CollisionResolver(track, CONFIG).move(ship, 0.1)
    assert ship.position.x == pytest.approx(4 + CONFIG.ship_width / 2, abs=1e-4)
    assert outcomes(reports) == [CollisionOutcome.SCRAPED_LEFT, CollisionOutcome.LANDED]


def test_free_strafing_does_not_scrape() -> None:
    ship = make_ship(velocity=Vector3(5, 0, 0))
    assert outcomes(CollisionResolver(make_track(FLAT), CONFIG).move(ship, 0.1)) == [CollisionOutcome.LANDED]


def test_falls_off_below_limit() -> None:
    ship = make_ship(y=CONFIG.fall_limit_y + 0.1, velocity=Vector3(0, -10, 0))
    track = make_track(".. .. .. .. .. .. .. ..")
    assert outcomes(CollisionResolver(track, CONFIG).move(ship, 0.02)) == [CollisionOutcome.FELL]


TUNNEL = ".. .. N1T N1T N1T N1T .. .."
ROUND_TUNNEL = ".. .. N1A N1A N1A N1A .. .."


@pytest.mark.parametrize("row", [TUNNEL, ROUND_TUNNEL])
def test_drives_into_a_tunnel(row: str) -> None:
    track = make_track(".. .. N1 N1 N1 N1 .. ..", row)
    ship = make_ship(x=4, velocity=Vector3(0, -0.1, 10))
    reports = CollisionResolver(track, CONFIG).move(ship, 0.05)
    assert outcomes(reports) == [CollisionOutcome.LANDED]
    assert ship.position.z == pytest.approx(1.0)


def test_flying_into_a_tunnel_roof_crashes() -> None:
    track = make_track(".. .. N1 N1 N1 N1 .. ..", TUNNEL)
    ship = make_ship(x=4, y=0.5 + TunnelSpan.CLEARANCE - 0.1, velocity=Vector3(0, 0, 10))
    assert outcomes(CollisionResolver(track, CONFIG).move(ship, 0.05)) == [CollisionOutcome.CRASHED]


@pytest.mark.parametrize("row", [TUNNEL, ROUND_TUNNEL])
def test_jumping_inside_a_tunnel_bumps_the_ceiling(row: str) -> None:
    track = make_track(row)
    ship = make_ship(x=4, velocity=Vector3(0, 20, 0))
    reports = CollisionResolver(track, CONFIG).move(ship, 0.1)
    assert outcomes(reports) == [CollisionOutcome.BUMPED]
    assert ship.velocity.y == 0
    box, tunnel = ship.bounding_box, track.tunnels[0]
    ceiling = min(tunnel.inner_height(box.minimum.x), tunnel.inner_height(box.maximum.x))
    assert ceiling - 0.25 < box.maximum.y < ceiling
    assert not ship.grounded


def test_tunnel_walls_stop_strafing() -> None:
    ship = make_ship(x=3, velocity=Vector3(-5, 0, 0))
    CollisionResolver(make_track(TUNNEL), CONFIG).move(ship, 0.2)
    assert ship.position.x == pytest.approx(2 + TunnelSpan.WALL + CONFIG.ship_width / 2, abs=1e-4)
    assert ship.velocity.x == 0


def test_lands_on_a_tunnel_roof_without_a_tile() -> None:
    roof = 0.5 + TunnelSpan.CLEARANCE + TunnelSpan.ROOF
    ship = make_ship(x=4, y=roof + 0.05, velocity=Vector3(0, -5, 0))
    reports = CollisionResolver(make_track(TUNNEL), CONFIG).move(ship, 0.02)
    assert outcomes(reports) == [CollisionOutcome.LANDED]
    assert reports[0].tile is None
    assert ship.position.y == pytest.approx(roof)


def test_covered_width_counts_overlapping_blockers_once() -> None:
    box = make_ship(x=4.5, width=1.0).bounding_box
    wide = Solid(BoundingBox(Vector3(3.5, 0, 0), Vector3(4.6, 1, 1)))
    inside = Solid(BoundingBox(Vector3(4.2, 0, 0), Vector3(4.4, 1, 1)))
    assert CollisionResolver._covered_width(box, [wide, inside]) == pytest.approx(0.6)  # noqa: SLF001
