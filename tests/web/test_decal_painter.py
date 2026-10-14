# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.web.decal_painter import DecalPainter
from tests.web.fakes.fake_js_bridge import FakeJsBridge

PATTERNS = ["chevrons-up", "chevrons-left", "stripes", "plus", "bubbles", "target", "crystal", "checker"]


@pytest.mark.parametrize("pattern", PATTERNS)
def test_paints_every_pattern_on_a_square_canvas(pattern: str) -> None:
    painter = DecalPainter(FakeJsBridge())
    canvas = painter.canvas(pattern)
    assert canvas.tag == "canvas"
    assert canvas.width == canvas.height == DecalPainter.SIZE
    context = canvas.context
    assert context.stroke.calls or context.strokeRect.calls or context.fillRect.calls


def test_canvases_are_painted_once() -> None:
    bridge = FakeJsBridge()
    painter = DecalPainter(bridge)
    assert painter.canvas("plus") is painter.canvas("plus")
    assert len(bridge.document.created) == 1


def test_chevrons_turn_toward_their_direction() -> None:
    painter = DecalPainter(FakeJsBridge())
    assert painter.canvas("chevrons-right").context.rotate.calls == [(DecalPainter.TURNS["right"],)]
