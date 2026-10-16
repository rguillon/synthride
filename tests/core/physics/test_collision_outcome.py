# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.physics.collision_outcome import CollisionOutcome


def test_outcomes() -> None:
    assert {outcome.name for outcome in CollisionOutcome} == {
        "LANDED",
        "BUMPED",
        "NUDGED",
        "SCRAPED_LEFT",
        "SCRAPED_RIGHT",
        "CRASHED",
        "FELL",
    }
