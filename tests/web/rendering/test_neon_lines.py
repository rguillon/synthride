# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.web.rendering.neon_lines import NeonLines
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def make_lines() -> tuple[FakeJsObject, NeonLines]:
    bridge = FakeJsBridge()
    return bridge.three, NeonLines(bridge)


def test_segments_are_thick_antialiased_fat_lines() -> None:
    three, lines = make_lines()
    line = lines.segments([0, 0, 0, 1, 0, 0], 0xFF00FF, 2.5)
    geometry, material = line.args
    assert geometry.setPositions.calls == [([0, 0, 0, 1, 0, 0],)]
    assert material.args[0] == {"color": 0xFF00FF, "linewidth": 2.5, "alphaToCoverage": True}
    assert three.LineSegments2.created == [line]


def test_edges_of_a_mesh_geometry() -> None:
    three, lines = make_lines()
    lines.edges_of("geometry", 0x00FFFF, 3)
    assert three.EdgesGeometry.created[0].args == ("geometry",)
    assert three.LineSegmentsGeometry.created[0].fromEdgesGeometry.calls == [(three.EdgesGeometry.created[0],)]


def test_new_lines_get_the_current_resolution_and_follow_resizes() -> None:
    _, lines = make_lines()
    first = lines.segments([], 1, 1)
    lines.resize(640, 480)
    second = lines.segments([], 1, 1)
    assert first.args[1].resolution.set.calls == [(1, 1), (640, 480)]
    assert second.args[1].resolution.set.calls == [(640, 480)]


def test_released_lines_stop_resizing() -> None:
    _, lines = make_lines()
    line = lines.segments([], 1, 1)
    lines.release(line)
    lines.release(line)
    lines.resize(10, 10)
    assert lines.count == 0
    assert line.args[1].resolution.set.calls == [(1, 1)]


def test_knows_which_lines_it_keeps_sized() -> None:
    lines = NeonLines(FakeJsBridge())
    line = lines.segments([0, 0, 0, 1, 1, 1], 0xFFFFFF, 2)
    assert line in lines
    lines.release(line)
    assert line not in lines
