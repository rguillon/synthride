# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.game_config import GameConfig
from tests.ai.track_reach import TrackReach


def test_apex_counts_the_double_jump() -> None:
    # (6.5² + 5.5²) / (2 * 18)
    assert TrackReach().apex(6.5) == pytest.approx(72.5 / 36)


def test_flight_time_back_to_take_off_height() -> None:
    # Up to the first apex, then a double jump from 6.5² / 36 high: (6.5 + 5.5 + sqrt(5.5² + 36 * 6.5² / 36)) / 18
    assert TrackReach().flight_time(6.5, 0.0) == pytest.approx((12 + 72.5**0.5) / 18)


def test_flight_time_is_none_above_the_surely_reached_height() -> None:
    reach = TrackReach()
    assert reach.flight_time(6.5, reach.margin * reach.apex(6.5) + 0.01) is None


def test_max_gap_at_top_speed() -> None:
    # Flying 0.65 of 1.1397s at 28 covers 20.74, less the ship's 0.8: 9 rows of 2.
    assert TrackReach().max_gap(6.5, 28.0, 0.0) == 9


def test_max_gap_shrinks_with_speed_and_rise() -> None:
    reach = TrackReach()
    assert reach.max_gap(6.5, 10.0, 0.0) < reach.max_gap(6.5, 28.0, 0.0)
    assert reach.max_gap(6.5, 28.0, 1.0) < reach.max_gap(6.5, 28.0, 0.0)
    assert reach.max_gap(6.5, 28.0, 5.0) == -1


def test_can_jump_agrees_with_max_gap() -> None:
    reach = TrackReach()
    longest = reach.max_gap(6.5, 20.0, 0.0)
    assert reach.can_jump(6.5, 20.0, longest, 0.0)
    assert not reach.can_jump(6.5, 20.0, longest + 1, 0.0)
    assert not reach.can_jump(6.5, 20.0, 0, 5.0)


def test_can_jump_from_further_back_reaches_less() -> None:
    reach = TrackReach()
    longest = reach.max_gap(6.5, 20.0, 0.0)
    assert not reach.can_jump(6.5, 20.0, longest, 0.0, extra=2.0)


def test_higher_gravity_shortens_jumps() -> None:
    assert TrackReach(gravity=24.0).max_gap(6.5, 28.0, 0.0) < TrackReach().max_gap(6.5, 28.0, 0.0)


def test_max_rise_levels() -> None:
    # floor(0.65 * 72.5 / 36 / 0.5) and floor(0.65 * (10² + 5.5²) / 36 / 0.5)
    assert TrackReach().max_rise_levels(6.5) == 2
    assert TrackReach().max_rise_levels(10.0) == 4


def test_next_speed_accelerates_up_to_the_cap() -> None:
    reach = TrackReach()
    # Accelerating at 14 over one row of 2.
    assert reach.next_speed(0.0, 28.0) == pytest.approx(56**0.5)
    assert reach.next_speed(27.9, 28.0) == 28.0
    assert reach.next_speed(20.0, reach.slow_speed) == pytest.approx(28.0 * 0.45)


def test_slow_speed_follows_the_config() -> None:
    assert TrackReach(GameConfig(max_speed=20.0, slow_factor=0.5)).slow_speed == 10.0
