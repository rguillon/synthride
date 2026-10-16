# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.gameplay.gauge import Gauge


def test_drains_and_refills() -> None:
    gauge = Gauge(10)
    assert gauge.is_full
    gauge.drain(4)
    assert gauge.fraction == pytest.approx(0.6)
    assert not gauge.is_full
    gauge.drain(100)
    assert gauge.value == 0
    assert gauge.is_empty
    gauge.refill()
    assert gauge.value == 10


def test_rejects_non_positive_capacity() -> None:
    with pytest.raises(ValueError, match="capacity must be positive"):
        Gauge(0)
