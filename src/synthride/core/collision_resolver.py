from __future__ import annotations

from synthride.core.bounding_box import BoundingBox
from synthride.core.collision_outcome import CollisionOutcome
from synthride.core.collision_report import CollisionReport
from synthride.core.game_config import GameConfig
from synthride.core.ship import Ship
from synthride.core.tile import Tile
from synthride.core.track import Track


class CollisionResolver:
    """Moves the ship through the track one axis at a time and resolves collisions.

    Lateral motion is blocked by walls. Forward motion into a wall is a crash when a large part of the
    ship's nose hits it, otherwise the ship is nudged sideways around the corner. Vertical motion lands
    the ship on tile tops. Dropping below the fall limit means the ship fell off the track.
    """

    EPSILON = 1e-6

    def __init__(self, track: Track, config: GameConfig) -> None:
        self._track = track
        self._config = config

    def move(self, ship: Ship, dt: float) -> list[CollisionReport]:
        self._move_laterally(ship, dt)
        reports = self._move_forward(ship, dt)
        if any(report.outcome is CollisionOutcome.CRASHED for report in reports):
            return reports
        reports.extend(self._move_vertically(ship, dt))
        if ship.position.y < self._config.fall_limit_y:
            reports.append(CollisionReport(CollisionOutcome.FELL))
        return reports

    def _blockers(self, box: BoundingBox) -> list[Tile]:
        floor = box.minimum.y + self._config.step_tolerance
        return [tile for tile in self._track.tiles_under(box) if tile.top > floor]

    def _move_laterally(self, ship: Ship, dt: float) -> None:
        vx = ship.velocity.x
        if vx == 0:
            return
        target = ship.position.with_x(ship.position.x + vx * dt)
        blockers = self._blockers(ship.box_at(target))
        if blockers:
            target = target.with_x(self._clear_x(ship, blockers, toward_positive=vx > 0))
            ship.velocity = ship.velocity.with_x(0.0)
        ship.position = target

    def _clear_x(self, ship: Ship, blockers: list[Tile], toward_positive: bool) -> float:
        """The x position that places the ship just beside ``blockers``."""
        half_width = ship.width / 2 + self.EPSILON
        if toward_positive:
            return min(tile.bounding_box.minimum.x for tile in blockers) - half_width
        return max(tile.bounding_box.maximum.x for tile in blockers) + half_width

    def _move_forward(self, ship: Ship, dt: float) -> list[CollisionReport]:
        target = ship.position.with_z(ship.position.z + ship.velocity.z * dt)
        box = ship.box_at(target)
        blockers = self._blockers(box)
        if not blockers:
            ship.position = target
            return []
        overlap_by_column = {tile.column: box.overlap_x(tile.bounding_box) for tile in blockers}
        if sum(overlap_by_column.values()) < self._config.crash_overlap_ratio * ship.width:
            nudged = self._nudge(ship, target, blockers)
            if nudged is not None:
                ship.position = nudged
                return [CollisionReport(CollisionOutcome.NUDGED, blockers[0])]
        front = min(tile.bounding_box.minimum.z for tile in blockers)
        ship.position = ship.position.with_z(min(ship.position.z, front - ship.length / 2 - self.EPSILON))
        ship.velocity = ship.velocity.with_z(0.0)
        return [CollisionReport(CollisionOutcome.CRASHED, blockers[0])]

    def _nudge(self, ship: Ship, target, blockers: list[Tile]):
        """Slides the ship sideways off a corner, or returns None when there is no room to do so."""
        sides = {tile.bounding_box.center_x > target.x for tile in blockers}
        if len(sides) != 1:
            return None
        nudged = target.with_x(self._clear_x(ship, blockers, toward_positive=sides.pop()))
        return None if self._blockers(ship.box_at(nudged)) else nudged

    def _move_vertically(self, ship: Ship, dt: float) -> list[CollisionReport]:
        old_y = ship.position.y
        new_y = old_y + ship.velocity.y * dt
        box = ship.box_at(ship.position.with_y(new_y))
        supports = [tile for tile in self._track.tiles_under(box) if tile.top <= old_y + self._config.step_tolerance]
        surface = max((tile.top for tile in supports), default=None)
        if surface is None or new_y > surface:
            ship.position = ship.position.with_y(new_y)
            ship.grounded = False
            return []
        ship.position = ship.position.with_y(surface)
        ship.velocity = ship.velocity.with_y(0.0)
        ship.grounded = True
        return [CollisionReport(CollisionOutcome.LANDED, self._tile_beneath(ship, supports, surface))]

    def _tile_beneath(self, ship: Ship, supports: list[Tile], surface: float) -> Tile:
        """Prefers the highest tile under the ship's centre, else any highest supporting tile."""
        highest = [tile for tile in supports if tile.top == surface]
        position = ship.position
        for tile in highest:
            minimum, maximum = tile.bounding_box.minimum, tile.bounding_box.maximum
            if minimum.x <= position.x < maximum.x and minimum.z <= position.z < maximum.z:
                return tile
        return highest[0]
