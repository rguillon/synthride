# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.game_config import GameConfig


def test_sane_defaults() -> None:
    config = GameConfig()
    assert 0 < config.fixed_step < 0.05
    assert 0 < config.crash_overlap_ratio < 1
    assert config.boost_factor > 1 > config.slow_factor > 0
    assert config.ship_width < 1, "the ship must fit between two towers"
    assert config.lives == 3
