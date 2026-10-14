import pytest

from synthride.core.level_parser import LevelParser
from synthride.core.tunnel_span import TunnelSpan
from synthride.web.neon_lines import NeonLines
from synthride.web.palette import Palette
from synthride.web.tunnel_mesh_builder import TunnelMeshBuilder
from tests.web.fakes.fake_js_bridge import FakeJsBridge


def build(*rows: str):
    bridge = FakeJsBridge()
    builder = TunnelMeshBuilder(bridge, NeonLines(bridge))
    parts = builder.build(LevelParser().parse("---\n" + "\n".join(rows)).track)
    return bridge.three, builder, parts


def segments(line) -> list[tuple[tuple[float, ...], tuple[float, ...]]]:
    positions = line.args[0].setPositions.calls[0][0]
    return [(tuple(positions[i : i + 3]), tuple(positions[i + 3 : i + 6])) for i in range(0, len(positions), 6)]


def test_no_tunnel_builds_nothing():
    three, builder, parts = build("N1 N1 N1 N1 N1 N1 N1 N1")
    assert parts == []
    assert builder.material is None
    assert three.Mesh.created == []


def test_one_shell_mesh_with_mouths_and_ribs():
    three, builder, parts = build(".. N1T N1T .. .. .. .. ..", ".. N1T N1T .. .. .. .. ..")
    assert len(parts) == 3
    assert parts[0] is three.Mesh.created[0]
    assert builder.material.args[0]["emissive"] == Palette.TUNNEL
    mouths, ribs = (segments(line) for line in three.LineSegments2.created)
    zs = {round(point[2], 2) for segment in mouths for point in segment}
    assert zs == {0.0, -1.0, -2.0}  # near mouth, ridge seam, far mouth
    assert {point[2] for segment in ribs for point in segment} == {-1.0}  # one ring between the two rows


def test_shell_is_closed_and_shaded_toward_the_outside():
    three, _, _ = build(".. N1T N1T .. .. .. .. ..")
    normals = three.BufferAttribute.created[1].args[0]
    positions = three.BufferAttribute.created[0].args[0]
    vertex_count = len(positions) // 3
    assert vertex_count == 3 * 4 * 6  # three segments, four faces each, six vertices per face
    roof_top = 0.5 + TunnelSpan.CLEARANCE + TunnelSpan.ROOF
    for index in range(vertex_count):
        if positions[3 * index + 1] == pytest.approx(roof_top) and normals[3 * index + 1] != 0:
            assert normals[3 * index + 1] == pytest.approx(1.0)


def test_round_tunnel_ridges_include_the_crown():
    three, _, _ = build(".. N1A N1A N1A .. .. .. ..")
    mouths = segments(three.LineSegments2.created[0])
    lengthwise = [segment for segment in mouths if segment[0][2] != segment[1][2]]
    assert len(lengthwise) == 3
    crown = max(segment[0][1] for segment in lengthwise)
    assert crown == pytest.approx(0.5 + TunnelSpan.SPRING + TunnelSpan.MAX_RISE + TunnelSpan.SHELL)
