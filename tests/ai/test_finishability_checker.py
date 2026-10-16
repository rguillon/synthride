# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.level_catalog import LevelCatalog
from tests.ai.finishability_checker import FinishabilityChecker
from tests.level_factory import make_level

LANE = ".. .. N1 N1 N1 N1 .. .."
EMPTY = ".. .. .. .. .. .. .. .."
NO_PATH = ["no safe path reaches the end of the track"]


def rows(line: str, count: int) -> str:
    return "\n".join([line] * count)


def check(*track: str, fuel_capacity: float = 100.0, oxygen_seconds: float = 90.0) -> list[str]:
    level = make_level(*track, fuel_capacity=fuel_capacity, oxygen_seconds=oxygen_seconds)
    return FinishabilityChecker().check(level)


def test_a_straight_track_is_finishable() -> None:
    assert check(rows(LANE, 20)) == []


@pytest.mark.parametrize("level", LevelCatalog().load_all(), ids=lambda level: level.name)
def test_every_bundled_level_is_finishable(level) -> None:  # noqa: ANN001
    assert FinishabilityChecker().check(level) == []


def test_the_ship_must_start_on_safe_tiles() -> None:
    problems = check(".. .. N1 .. .. N1 .. ..", rows(LANE, 5))
    assert problems == ["the ship starts over columns (3, 4): they need flat safe tiles of one height"]


def test_a_short_gap_can_be_jumped() -> None:
    assert check(rows(LANE, 30), rows(EMPTY, 3), rows(LANE, 5)) == []


def test_a_long_gap_cannot_be_jumped() -> None:
    assert check(rows(LANE, 30), rows(EMPTY, 15), rows(LANE, 5)) == NO_PATH


def test_a_gap_right_after_the_start_is_too_long_without_speed() -> None:
    assert check(rows(LANE, 1), rows(EMPTY, 6), rows(LANE, 5)) == NO_PATH
    assert check(rows(LANE, 30), rows(EMPTY, 6), rows(LANE, 5)) == []


def test_a_jump_lands_at_most_one_column_aside() -> None:
    near = ".. .. .. .. .. .. N1 .."
    far = ".. .. .. .. .. .. .. N1"
    assert check(rows(LANE, 30), rows(EMPTY, 2), rows(near, 5)) == []
    assert check(rows(LANE, 30), rows(EMPTY, 2), rows(far, 5)) == NO_PATH


def test_a_few_kill_rows_can_be_jumped_but_not_ridden() -> None:
    kill = ".. .. K1 K1 K1 K1 .. .."
    assert check(rows(LANE, 30), kill, rows(LANE, 5)) == []
    assert check(rows(LANE, 30), rows(kill, 20), rows(LANE, 5)) == NO_PATH


def test_a_safe_window_through_kill_tiles() -> None:
    window = ".. .. K1 K1 N1 K1 .. .."
    assert check(rows(LANE, 30), rows(window, 20), rows(LANE, 5)) == []


def test_the_ship_can_slide_sideways_on_a_row() -> None:
    assert check(rows(LANE, 5), ".. .. N1 N1 N1 N1 N1 N1", rows(".. .. .. .. .. .. .. N1", 20)) == []


def test_a_step_up_needs_a_jump_within_reach() -> None:
    assert check(rows(LANE, 10), rows(".. .. N3 N3 N3 N3 .. ..", 5)) == []
    assert check(rows(LANE, 10), rows(".. .. N4 N4 N4 N4 .. ..", 5)) == NO_PATH


def test_ramps_climb_without_jumping() -> None:
    ramps = [f".. .. N{level}f N{level}f N{level}f N{level}f .. .." for level in range(1, 6)]
    assert check(rows(LANE, 2), *ramps, rows(".. .. N6 N6 N6 N6 .. ..", 5)) == []


def test_a_jump_pad_launches_further() -> None:
    pad = ".. .. J1 J1 J1 J1 .. .."
    assert check(rows(LANE, 30), rows(EMPTY, 12), rows(LANE, 5)) == NO_PATH
    assert check(rows(LANE, 30), pad, rows(EMPTY, 12), rows(LANE, 5)) == []


def test_slow_tiles_shorten_jumps() -> None:
    slow = ".. .. S1 S1 S1 S1 .. .."
    assert check(rows(LANE, 30), rows(EMPTY, 6), rows(LANE, 5)) == []
    assert check(rows(LANE, 30), rows(slow, 5), rows(EMPTY, 6), rows(LANE, 5)) == NO_PATH


def test_no_jumping_under_a_tunnel_roof() -> None:
    tunnel = ".. .. N1T N1T N1T N1T .. .."
    assert check(rows(LANE, 30), rows(tunnel, 5), ".. .. N1T N1T N1T N1T .. ..", rows(LANE, 5)) == []
    assert check(rows(LANE, 30), rows(tunnel, 5), rows(EMPTY, 3), rows(LANE, 5)) == []
    assert check(rows(LANE, 30), rows(".. .. N1T N1 N1 N1 .. ..", 1), rows(LANE, 5)) == []


def test_a_one_column_tunnel_is_too_narrow_to_enter() -> None:
    narrow = ".. .. .. N1T .. .. .. .."
    wide = ".. .. .. N1T N1T .. .. .."
    assert check(rows(LANE, 5), rows(narrow, 20), rows(LANE, 5)) == NO_PATH
    assert check(rows(LANE, 5), rows(wide, 20), rows(LANE, 5)) == []


def test_a_finish_tile_ends_the_run_early() -> None:
    finish = ".. .. F1 F1 F1 F1 .. .."
    assert check(rows(LANE, 5), finish, rows(EMPTY, 30), rows(LANE, 5)) == []


def test_not_enough_fuel_or_oxygen() -> None:
    problems = check(rows(LANE, 100), fuel_capacity=10.0, oxygen_seconds=5.0)
    assert len(problems) == 2
    assert problems[0].startswith("needs 25.0 fuel, has 10.0")
    assert "oxygen" in problems[1]


def test_refills_on_the_path_split_the_needs() -> None:
    refills = ".. .. R1 R1 O1 O1 .. .."
    checker = FinishabilityChecker()
    whole = checker.requirements(make_level(rows(LANE, 100)))
    split = checker.requirements(make_level(rows(LANE, 50), refills, rows(LANE, 49)))
    assert whole is not None
    assert split is not None
    assert split.fuel < whole.fuel
    assert split.oxygen_seconds < whole.oxygen_seconds


def test_no_requirements_without_a_path() -> None:
    assert FinishabilityChecker().requirements(make_level(rows(LANE, 5), rows(EMPTY, 30), rows(LANE, 5))) is None
