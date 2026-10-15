# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.ai.ship_observer import ShipObserver
from synthride.core.game_session import GameSession
from tests.level_factory import make_level

TRACK = (
    ".. .. .. N1 N1 N1 .. ..",
    ".. .. .. K1 N3 J1 .. ..",
    ".. .. .. <1 N1T >1 .. ..",
    ".. .. .. B1 N1 I1 .. ..",
)


def cell(inputs: list[float], ahead: int, side: int) -> list[float]:
    start = ShipObserver.SHIP_FEATURES + (ahead * ShipObserver.COLUMNS + side + 2) * ShipObserver.CELL_FEATURES
    return inputs[start : start + ShipObserver.CELL_FEATURES]


def test_observes_the_ship_and_the_track_ahead() -> None:
    session = GameSession([make_level(*TRACK)])
    session.start()
    inputs = ShipObserver().observe(session)
    assert len(inputs) == ShipObserver.SIZE
    assert inputs[0] == pytest.approx(0.0)  # centred on the track
    assert inputs[6:10] == [1.0, 0.0, 1.0, 1.0]  # grounded, no air jump yet, full gauges
    assert cell(inputs, 0, 0) == [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert cell(inputs, 0, 2) == list(ShipObserver.EMPTY)
    assert cell(inputs, 1, -1) == [1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]  # kill
    assert cell(inputs, 1, 0)[1] == pytest.approx(0.5)  # one unit higher
    assert cell(inputs, 1, 1)[4] == 1.0  # jump pad
    assert cell(inputs, 2, -1)[5] == -1.0  # pushes left
    assert cell(inputs, 2, 0)[3] == 1.0  # tunnel
    assert cell(inputs, 2, 1)[5] == 1.0  # pushes right
    assert cell(inputs, 3, -1)[6] == 1.0  # boost
    assert cell(inputs, 3, 1)[6] == -1.0  # ice
    assert cell(inputs, 4, 0) == list(ShipObserver.EMPTY)  # past the end
