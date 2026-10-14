# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.collision_outcome import CollisionOutcome
from synthride.core.collision_report import CollisionReport


def test_tile_is_optional() -> None:
    assert CollisionReport(CollisionOutcome.FELL).tile is None
