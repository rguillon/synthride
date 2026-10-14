# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import math
import random

import pytest

from synthride.core.game_event import GameEvent
from synthride.core.ship import Ship
from synthride.core.vector3 import Vector3
from synthride.web.neon_sparks import NeonSparks
from tests.web.fakes.fake_js_bridge import FakeJsBridge


def make_sparks() -> NeonSparks:
    return NeonSparks(FakeJsBridge(), rng=random.Random(7))  # noqa: S311


def writes(sparks: NeonSparks, name: str) -> list[tuple]:
    attribute, _ = sparks._attributes[name]  # noqa: SLF001
    return attribute.array.set.calls


def test_starts_with_every_spark_dead_and_never_culled() -> None:
    sparks = make_sparks()
    births, _ = sparks._attributes["aBirth"]  # noqa: SLF001
    assert set(births.args[0]) == {-1e6}
    assert len(births.args[0]) == NeonSparks.CAPACITY
    assert sparks.points.frustumCulled is False


def test_quiet_frames_emit_nothing() -> None:
    sparks = make_sparks()
    sparks.react([GameEvent.LANDED, GameEvent.JUMPED], Ship(Vector3()))
    assert writes(sparks, "position") == []


@pytest.mark.parametrize(("event", "side"), [(GameEvent.SCRAPED_LEFT, -1), (GameEvent.SCRAPED_RIGHT, 1)])
def test_scraping_showers_sparks_off_the_wall_side(event: GameEvent, side: int) -> None:
    sparks = make_sparks()
    ship = Ship(Vector3(4, 1, 10))
    sparks.react([event, event], ship)
    calls = writes(sparks, "position")
    assert [offset for _, offset in calls] == [0, 3 * NeonSparks.SCRAPE.count]
    xs = calls[0][0][0::3]
    assert xs == [4 + side * ship.width / 2] * NeonSparks.SCRAPE.count
    assert calls[0][0][2] == -10  # world z runs the other way
    velocities = writes(sparks, "aVelocity")[0][0]
    assert all(vx * side <= 0 for vx in velocities[0::3])  # back toward the track


def test_crashing_bursts_far_more_sparks_than_a_scrape() -> None:
    sparks = make_sparks()
    sparks.react([GameEvent.CRASHED], Ship(Vector3()))
    ((values, _),) = writes(sparks, "aBirth")
    assert len(values) == NeonSparks.DEATH.count > 10 * NeonSparks.SCRAPE.count
    speeds = [math.dist((0, 0, 0), v) for v in zip(*[iter(writes(sparks, "aVelocity")[0][0])] * 3, strict=True)]
    assert max(speeds) <= NeonSparks.DEATH.speed[1]


def test_sparks_are_born_on_the_spark_clock() -> None:
    sparks = make_sparks()
    sparks.update(1.5)
    assert sparks.material.uniforms.uTime.value == 1.5
    sparks.react([GameEvent.NUDGED], Ship(Vector3()))
    assert set(writes(sparks, "aBirth")[0][0]) == {1.5}


def test_ring_buffer_wraps_around() -> None:
    sparks = make_sparks()
    ship = Ship(Vector3())
    for _ in range(NeonSparks.CAPACITY // NeonSparks.DEATH.count + 1):
        sparks.react([GameEvent.CRASHED], ship)
    offsets = [offset for _, offset in writes(sparks, "aLife")]
    assert offsets[-1] == 0
    assert all(offset + NeonSparks.DEATH.count <= NeonSparks.CAPACITY for offset in offsets)
