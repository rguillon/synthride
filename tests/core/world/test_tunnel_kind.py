# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.world.tunnel_kind import TunnelKind


def test_letters() -> None:
    assert TunnelKind("T") is TunnelKind.SQUARE
    assert TunnelKind("A") is TunnelKind.ROUND
