# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.web.ui.fps_counter import FpsCounter


def test_reports_the_average_rate_once_per_window() -> None:
    counter = FpsCounter()
    assert counter.fps is None
    readings = [counter.record(1 / 64) for _ in range(32)]
    assert readings == [False] * 31 + [True]
    assert counter.fps == pytest.approx(64)


def test_starts_a_fresh_window_after_each_reading() -> None:
    counter = FpsCounter()
    counter.record(FpsCounter.WINDOW_SECONDS)
    assert counter.fps == pytest.approx(2)
    assert not counter.record(0.1)
    assert counter.record(FpsCounter.WINDOW_SECONDS)
    assert counter.fps == pytest.approx(2 / (0.1 + FpsCounter.WINDOW_SECONDS))
