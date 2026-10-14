# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Moving the ship through the track and resolving its collisions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.core.collision_outcome import CollisionOutcome
from synthride.core.collision_report import CollisionReport

if TYPE_CHECKING:
    from synthride.core.bounding_box import BoundingBox
    from synthride.core.game_config import GameConfig
    from synthride.core.ship import Ship
    from synthride.core.solid import Solid
    from synthride.core.tile import Tile
    from synthride.core.track import Track
    from synthride.core.vector3 import Vector3


class CollisionResolver:
    """Moves the ship through the track one axis at a time and resolves collisions.

    The ship collides with solids: tile blocks and the pieces of tunnel shells. Lateral motion is blocked
    by walls. Forward motion into a wall is a crash when a large part of the ship's nose hits it, otherwise
    the ship is nudged sideways around the corner. Vertical motion lands the ship on tops and bumps it
    against ceilings. Dropping below the fall limit means the ship fell off the track.
    """

    EPSILON = 1e-6

    def __init__(self, track: Track, config: GameConfig) -> None:
        """Resolve collisions against the solids of ``track``."""
        self._track = track
        self._config = config

    def move(self, ship: Ship, dt: float) -> list[CollisionReport]:
        """Move the ship by its velocity for ``dt`` seconds and report what it hit."""
        reports = self._move_laterally(ship, dt)
        reports += self._move_forward(ship, dt)
        if any(report.outcome is CollisionOutcome.CRASHED for report in reports):
            return reports
        reports.extend(self._move_vertically(ship, dt))
        if ship.position.y < self._config.fall_limit_y:
            reports.append(CollisionReport(CollisionOutcome.FELL))
        return reports

    def _blockers(self, box: BoundingBox) -> list[Solid]:
        """Solids in the way of ``box``: those that rise above a small step and start below its top."""
        floor = box.minimum.y + self._config.step_tolerance
        return [
            solid
            for solid in self._track.solids_under(box)
            if solid.box.maximum.y > floor and solid.box.minimum.y < box.maximum.y - self.EPSILON
        ]

    def _move_laterally(self, ship: Ship, dt: float) -> list[CollisionReport]:
        """Strafes the ship, reporting a scrape on the side of any wall that stops it."""
        vx = ship.velocity.x
        if vx == 0:
            return []
        target = ship.position.with_x(ship.position.x + vx * dt)
        blockers = self._blockers(ship.box_at(target))
        if not blockers:
            ship.position = target
            return []
        ship.position = target.with_x(self._clear_x(ship, blockers, toward_positive=vx > 0))
        ship.velocity = ship.velocity.with_x(0.0)
        return [CollisionReport(CollisionOutcome.SCRAPED_RIGHT if vx > 0 else CollisionOutcome.SCRAPED_LEFT)]

    def _clear_x(self, ship: Ship, blockers: list[Solid], *, toward_positive: bool) -> float:
        """Return the x position that places the ship just beside ``blockers``."""
        half_width = ship.width / 2 + self.EPSILON
        if toward_positive:
            return min(solid.box.minimum.x for solid in blockers) - half_width
        return max(solid.box.maximum.x for solid in blockers) + half_width

    def _move_forward(self, ship: Ship, dt: float) -> list[CollisionReport]:
        target = ship.position.with_z(ship.position.z + ship.velocity.z * dt)
        box = ship.box_at(target)
        blockers = self._blockers(box)
        if not blockers:
            ship.position = target
            return []
        if self._covered_width(box, blockers) < self._config.crash_overlap_ratio * ship.width:
            nudged = self._nudge(ship, target, blockers)
            if nudged is not None:
                ship.position = nudged
                return [CollisionReport(CollisionOutcome.NUDGED, blockers[0].tile)]
        front = min(solid.box.minimum.z for solid in blockers)
        ship.position = ship.position.with_z(min(ship.position.z, front - ship.length / 2 - self.EPSILON))
        ship.velocity = ship.velocity.with_z(0.0)
        return [CollisionReport(CollisionOutcome.CRASHED, blockers[0].tile)]

    @staticmethod
    def _covered_width(box: BoundingBox, blockers: list[Solid]) -> float:
        """How much of the width of ``box`` the blockers cover, counting overlapping blockers once."""
        spans = sorted(
            (max(box.minimum.x, solid.box.minimum.x), min(box.maximum.x, solid.box.maximum.x)) for solid in blockers
        )
        covered, reach = 0.0, box.minimum.x
        for start, end in spans:
            if end > reach:
                covered += end - max(start, reach)
                reach = end
        return covered

    def _nudge(self, ship: Ship, target: Vector3, blockers: list[Solid]) -> Vector3 | None:
        """Slides the ship sideways off a corner, or returns None when there is no room to do so."""
        sides = {solid.box.center_x > target.x for solid in blockers}
        if len(sides) != 1:
            return None
        nudged = target.with_x(self._clear_x(ship, blockers, toward_positive=sides.pop()))
        return None if self._blockers(ship.box_at(nudged)) else nudged

    def _move_vertically(self, ship: Ship, dt: float) -> list[CollisionReport]:
        old_y = ship.position.y
        new_y = old_y + ship.velocity.y * dt
        if new_y > old_y:
            return self._move_up(ship, old_y, new_y)
        box = ship.box_at(ship.position.with_y(new_y))
        supports = [
            solid
            for solid in self._track.solids_under(box)
            if solid.box.maximum.y <= old_y + self._config.step_tolerance
        ]
        surface = max((solid.box.maximum.y for solid in supports), default=None)
        if surface is None or new_y > surface:
            ship.position = ship.position.with_y(new_y)
            ship.grounded = False
            return []
        ship.position = ship.position.with_y(surface)
        ship.velocity = ship.velocity.with_y(0.0)
        ship.grounded = True
        return [CollisionReport(CollisionOutcome.LANDED, self._tile_beneath(ship, supports, surface))]

    def _move_up(self, ship: Ship, old_y: float, new_y: float) -> list[CollisionReport]:
        """Rises toward ``new_y``, stopping under any ceiling in the way."""
        ship.grounded = False
        old_top = old_y + ship.height
        box = ship.box_at(ship.position.with_y(new_y))
        ceilings = [
            solid
            for solid in self._track.solids_under(box)
            if old_top - self.EPSILON <= solid.box.minimum.y < box.maximum.y
        ]
        if not ceilings:
            ship.position = ship.position.with_y(new_y)
            return []
        ceiling = min(solid.box.minimum.y for solid in ceilings)
        ship.position = ship.position.with_y(max(old_y, ceiling - ship.height - self.EPSILON))
        ship.velocity = ship.velocity.with_y(0.0)
        return [CollisionReport(CollisionOutcome.BUMPED)]

    def _tile_beneath(self, ship: Ship, supports: list[Solid], surface: float) -> Tile | None:
        """Return the tile of the highest solid under the ship's centre, else of any highest support.

        None when the ship rests on a tunnel's shell, which has no effect.
        """
        highest = [solid for solid in supports if solid.box.maximum.y == surface]
        position = ship.position
        for solid in highest:
            minimum, maximum = solid.box.minimum, solid.box.maximum
            if minimum.x <= position.x < maximum.x and minimum.z <= position.z < maximum.z:
                return solid.tile
        return highest[0].tile
