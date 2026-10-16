# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.physics.collision_outcome import CollisionOutcome
from synthride.core.physics.collision_report import CollisionReport


def test_tile_is_optional() -> None:
    assert CollisionReport(CollisionOutcome.FELL).tile is None
