# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.gameplay.ship_input import ShipInput


def test_defaults_to_no_command() -> None:
    assert ShipInput() == ShipInput(accelerate=False, brake=False, left=False, right=False, jump=False)
