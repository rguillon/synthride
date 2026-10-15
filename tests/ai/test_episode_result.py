# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.ai.episode_result import EpisodeResult


def test_score_rewards_progress_then_fast_wins() -> None:
    assert EpisodeResult(0.4, won=False, seconds=10).score == pytest.approx(0.4)
    slow, fast = EpisodeResult(1.0, won=True, seconds=60), EpisodeResult(1.0, won=True, seconds=20)
    assert 2.0 < slow.score < fast.score < 3.0
