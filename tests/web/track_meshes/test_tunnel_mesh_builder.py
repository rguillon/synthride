# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.world.tunnel_span import TunnelSpan
from synthride.web.rendering.neon_lines import NeonLines
from synthride.web.rendering.palette import Palette
from synthride.web.track_meshes.tunnel_mesh_builder import TunnelMeshBuilder
from tests.level_factory import make_level
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def build(*rows: str) -> tuple[FakeJsObject, TunnelMeshBuilder, list[FakeJsObject]]:
    bridge = FakeJsBridge()
    builder = TunnelMeshBuilder(bridge, NeonLines(bridge))
    parts = builder.build(make_level(*rows).track)
    return bridge.three, builder, parts


def segments(line: FakeJsObject) -> list[tuple[tuple[float, ...], tuple[float, ...]]]:
    positions = line.args[0].setPositions.calls[0][0]
    return [(tuple(positions[i : i + 3]), tuple(positions[i + 3 : i + 6])) for i in range(0, len(positions), 6)]


def test_no_tunnel_builds_nothing() -> None:
    three, builder, parts = build("N1 N1 N1 N1 N1 N1 N1 N1")
    assert parts == []
    assert builder.material is None
    assert three.Mesh.created == []


def test_one_shell_mesh_with_mouths_and_ribs() -> None:
    three, builder, parts = build(".. N1T N1T .. .. .. .. ..", ".. N1T N1T .. .. .. .. ..")
    assert len(parts) == 3
    assert parts[0] is three.Mesh.created[0]
    assert builder.material.args[0]["emissive"] == Palette.TUNNEL
    mouths, ribs = (segments(line) for line in three.LineSegments2.created)
    zs = {round(point[2], 2) for segment in mouths for point in segment}
    assert zs == {0.0, -2.0, -4.0}  # near mouth, ridge seam, far mouth
    # One ring in the middle of each row, like the deck's seams, and one between the two rows.
    assert {point[2] for segment in ribs for point in segment} == {-1.0, -2.0, -3.0}


def test_shell_is_closed_and_shaded_toward_the_outside() -> None:
    three, _, _ = build(".. N1T N1T .. .. .. .. ..")
    normals = three.BufferAttribute.created[1].args[0]
    positions = three.BufferAttribute.created[0].args[0]
    vertex_count = len(positions) // 3
    assert vertex_count == 3 * 4 * 6  # three segments, four faces each, six vertices per face
    roof_top = 0.5 + TunnelSpan.CLEARANCE + TunnelSpan.ROOF
    for index in range(vertex_count):
        if positions[3 * index + 1] == pytest.approx(roof_top) and normals[3 * index + 1] != 0:
            assert normals[3 * index + 1] == pytest.approx(1.0)


def test_round_tunnel_ridges_include_the_crown() -> None:
    three, _, _ = build(".. N1A N1A N1A .. .. .. ..")
    mouths = segments(three.LineSegments2.created[0])
    lengthwise = [segment for segment in mouths if segment[0][2] != segment[1][2]]
    assert len(lengthwise) == 3
    crown = max(segment[0][1] for segment in lengthwise)
    assert crown == pytest.approx(0.5 + TunnelSpan.SPRING + TunnelSpan.MAX_RISE + TunnelSpan.SHELL)
