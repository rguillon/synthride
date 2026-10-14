# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.tunnel_kind import TunnelKind
from synthride.core.tunnel_span import TunnelSpan


def span(kind: TunnelKind = TunnelKind.ROUND, first: int = 2, last: int = 5, deck: float = 0.5) -> TunnelSpan:
    return TunnelSpan(kind, 3, first, last, deck)


def test_extent() -> None:
    tunnel = span()
    assert (tunnel.left, tunnel.right, tunnel.center, tunnel.half_width) == (2, 6, 4, 2)
    assert tunnel.rise == TunnelSpan.MAX_RISE
    assert span(first=2, last=2).rise == pytest.approx(0.5 - TunnelSpan.WALL)


def test_paths_pair_up_and_stand_on_the_deck() -> None:
    for kind in TunnelKind:
        tunnel = span(kind)
        outer, inner = tunnel.outer_path(), tunnel.inner_path()
        assert len(outer) == len(inner)
        assert outer[0] == (2, 0.5)
        assert outer[-1] == (6, 0.5)
        assert inner[0] == (2 + TunnelSpan.WALL, 0.5)
        assert all(y_out >= y_in for (_, y_out), (_, y_in) in zip(outer[1:-1], inner[1:-1], strict=True))


def test_round_paths_follow_the_arch() -> None:
    tunnel = span()
    crown = tunnel.inner_path()[1 + TunnelSpan.ARCH_SEGMENTS // 2]
    assert crown == pytest.approx((4, 0.5 + TunnelSpan.SPRING + TunnelSpan.MAX_RISE))
    assert tunnel.inner_height(4) == pytest.approx(crown[1])
    assert tunnel.outer_height(4) == pytest.approx(crown[1] + TunnelSpan.SHELL)
    assert tunnel.inner_height(2.1) == pytest.approx(0.5 + TunnelSpan.SPRING)


def test_square_solids_are_two_walls_and_a_roof() -> None:
    walls_and_roof = span(TunnelKind.SQUARE).solids()
    assert len(walls_and_roof) == 3
    roof = walls_and_roof[2].box
    assert roof.minimum.y == pytest.approx(0.5 + TunnelSpan.CLEARANCE)
    assert (roof.minimum.z, roof.maximum.z) == (3, 4)
    assert all(solid.tile is None for solid in walls_and_roof)


def test_round_roof_slices_stay_under_the_arch() -> None:
    tunnel = span()
    slices = tunnel.solids()[2:]
    assert slices[0].box.minimum.x == pytest.approx(2 + TunnelSpan.WALL)
    assert slices[-1].box.maximum.x == pytest.approx(6 - TunnelSpan.WALL)
    for solid in slices:
        box = solid.box
        assert box.maximum.x - box.minimum.x <= TunnelSpan.SLICE_WIDTH + 1e-9
        assert box.minimum.y <= min(tunnel.inner_height(box.minimum.x), tunnel.inner_height(box.maximum.x)) + 1e-9
        assert box.maximum.y >= max(tunnel.outer_height(box.minimum.x), tunnel.outer_height(box.maximum.x)) - 1e-9


def test_continues_only_the_same_tunnel() -> None:
    tunnel = span()
    assert tunnel.continues(TunnelSpan(TunnelKind.ROUND, 4, 2, 5, 0.5))
    assert not tunnel.continues(None)
    assert not tunnel.continues(span(TunnelKind.SQUARE))
    assert not tunnel.continues(span(deck=1.0))
    assert not tunnel.continues(span(last=6))
