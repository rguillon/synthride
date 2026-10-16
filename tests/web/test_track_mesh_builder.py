# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.tile_type import TileType
from synthride.web.neon_lines import NeonLines
from synthride.web.palette import Palette
from synthride.web.ship_reflection import ShipReflection
from synthride.web.track_mesh_builder import TrackMeshBuilder
from tests.level_factory import make_level
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def build(rows: str) -> tuple[FakeJsObject, TrackMeshBuilder, FakeJsObject, NeonLines]:
    bridge = FakeJsBridge()
    lines = NeonLines(bridge)
    builder = TrackMeshBuilder(bridge, lines)
    group = builder.build(make_level(rows).track)
    return bridge.three, builder, group, lines


def rails_of(
    three: FakeJsObject, color: int, width: float | None = None
) -> set[tuple[tuple[float, ...], tuple[float, ...]]]:
    """Segments (start, end) of the line set drawn in ``color`` (and ``width``, if given)."""
    for line, material in zip(three.LineSegments2.created, three.LineMaterial.created, strict=True):
        options = material.args[0]
        if options["color"] == color and width in (None, options["linewidth"]):
            positions = line.args[0].setPositions.calls[0][0]
            return {(tuple(positions[i : i + 3]), tuple(positions[i + 3 : i + 6])) for i in range(0, len(positions), 6)}
    return set()


def test_one_mesh_per_tile_type_one_rail_set_per_colour_plus_seams() -> None:
    three, _, group, _ = build("N1 N1 K1 .. .. .. .. ..\nN2 B1 .. .. .. .. .. ..")
    assert len(three.Mesh.created) == 6  # three tile types, plus normal, kill and boost markings
    assert len(three.MeshBasicMaterial.created) == 3
    assert len(three.LineSegments2.created) == 4
    assert (
        len(group.add.calls) == 8
    )  # meshes, rail sets (kill rails join the normal ones), seams, kill outline, markings
    widths = sorted(m.args[0]["linewidth"] for m in three.LineMaterial.created)
    assert (
        widths == [TrackMeshBuilder.SEAM_WIDTH, TrackMeshBuilder.KILL_OUTLINE_WIDTH] + [TrackMeshBuilder.LINE_WIDTH] * 2
    )
    emissive = sorted(material.args[0]["emissive"] for material in three.MeshStandardMaterial.created)
    assert emissive == sorted(Palette.tile_color(t) for t in (TileType.NORMAL, TileType.KILL, TileType.BOOST))
    assert all(material.args[0]["vertexColors"] for material in three.MeshStandardMaterial.created)


def test_rails_only_trace_edges_that_drop_away() -> None:
    three, _, _, _ = build("N1 N1 .. .. .. .. .. ..")
    y = 0.5 + TrackMeshBuilder.LINE_LIFT
    rails = rails_of(three, Palette.tile_color(TileType.NORMAL))
    assert len(rails) == 6  # the perimeter of a 2x1 strip, not the shared edge
    assert ((1.0, y, 0.0), (1.0, y, -2.0)) not in rails
    assert rails_of(three, TrackMeshBuilder.SEAM_COLOR) == {
        ((1.0, y, 0.0), (1.0, y, -2.0)),
        ((0.0, y, -1.0), (1.0, y, -1.0)),  # each tile is drawn as two squares
        ((1.0, y, -1.0), (2.0, y, -1.0)),
    }


def test_step_up_rails_belong_to_the_higher_tile() -> None:
    three, _, _, _ = build("N1 N2 .. .. .. .. .. ..")
    rails = rails_of(three, Palette.tile_color(TileType.NORMAL))
    low, high = 0.5 + TrackMeshBuilder.LINE_LIFT, 1.0 + TrackMeshBuilder.LINE_LIFT
    assert ((1.0, high, 0.0), (1.0, high, -2.0)) in rails
    assert len(rails) == 7
    assert rails_of(three, TrackMeshBuilder.SEAM_COLOR) == {
        ((0.0, low, -1.0), (1.0, low, -1.0)),
        ((1.0, high, -1.0), (2.0, high, -1.0)),
    }


def test_geometry_is_mirrored_along_z() -> None:
    three, _, _, _ = build("N1 .. .. .. .. .. .. ..")
    positions = three.BufferAttribute.created[0].args[0]
    zs = positions[2::3]
    assert max(zs) == 0
    assert min(zs) == -2


def test_animate_pulses_special_tiles_only() -> None:
    three, builder, _, _ = build("N1 K1 .. .. .. .. .. ..")
    builder.animate(0.3)
    normal, kill = three.MeshStandardMaterial.created
    assert isinstance(kill.emissiveIntensity, float)
    assert kill.emissiveIntensity >= TrackMeshBuilder.BODY_GLOW
    assert not isinstance(normal.emissiveIntensity, float)


def test_rebuilding_releases_previous_outlines() -> None:
    _, builder, _, lines = build("N1 K1 .. .. .. .. .. ..")
    builder.build(make_level("N1 " * 8).track)
    assert lines.count == 2  # one rail set and the seams


def test_tunnels_join_the_track_and_their_outlines_are_released_on_rebuild() -> None:
    three, builder, _, lines = build("N1T N1T .. .. .. .. .. ..\nN1T N1T .. .. .. .. .. ..")
    assert len(three.MeshStandardMaterial.created) == 2  # tiles and tunnel shell
    assert lines.count == 4  # tile rails, seams, tunnel mouths and ribs
    builder.build(make_level("N1 " * 8).track)
    assert lines.count == 2


def test_tile_type_without_drop_has_no_rails() -> None:
    three, _, _, _ = build("N1 N1 N1 .. .. .. .. ..\nN1 B1 N1 .. .. .. .. ..\nN1 N1 N1 .. .. .. .. ..")
    assert rails_of(three, Palette.tile_color(TileType.BOOST)) == set()
    assert len(three.LineSegments2.created) == 2  # normal rails and seams only


def test_solids_are_pushed_behind_their_lines() -> None:
    three, _, _, _ = build("N1T K1 .. .. .. .. .. ..")
    assert all(material.args[0]["polygonOffset"] for material in three.MeshStandardMaterial.created)
    assert all(material.args[0]["polygonOffsetFactor"] > 0 for material in three.MeshStandardMaterial.created)


def test_a_ramp_joins_the_tiles_it_links_without_rails() -> None:
    three, _, _, _ = build(".. .. .. N1 .. .. .. ..\n.. .. .. N1f .. .. .. ..\n.. .. .. N2 .. .. .. ..")
    lift = TrackMeshBuilder.LINE_LIFT
    seams = rails_of(three, TrackMeshBuilder.SEAM_COLOR)
    assert ((3.0, 0.5 + lift, -2.0), (4.0, 0.5 + lift, -2.0)) in seams
    assert ((3.0, 1.0 + lift, -4.0), (4.0, 1.0 + lift, -4.0)) in seams
    assert ((3.0, 0.75 + lift, -3.0), (4.0, 0.75 + lift, -3.0)) in seams  # halfway up the ramp
    rails = rails_of(three, Palette.tile_color(TileType.NORMAL))
    assert ((3.0, 0.5 + lift, -2.0), (3.0, 1.0 + lift, -4.0)) in rails  # the ramp's slanted side


def test_a_ramp_drops_away_from_the_flat_tile_beside_its_low_end() -> None:
    three, _, _, _ = build(".. .. .. N1 N1f .. .. ..")
    lift = TrackMeshBuilder.LINE_LIFT
    rails = rails_of(three, Palette.tile_color(TileType.NORMAL))
    assert ((4.0, 1.0 + lift, -2.0), (4.0, 0.5 + lift, 0.0)) not in rails
    assert ((4.0, 0.5 + lift, 0.0), (4.0, 1.0 + lift, -2.0)) in rails


def test_corner_slopes_are_sloped_and_marked_along_their_crease() -> None:
    three, _, _, _ = build(".. .. .. N1fr N1fl .. .. ..")
    positions = three.BufferAttribute.created[0].args[0]
    assert max(positions[1::3]) == 1.0
    lift = TrackMeshBuilder.LINE_LIFT
    seams = rails_of(three, TrackMeshBuilder.SEAM_COLOR)
    assert ((3.0, 0.5 + lift, 0.0), (4.0, 1.0 + lift, -2.0)) in seams
    assert ((5.0, 0.5 + lift, 0.0), (4.0, 1.0 + lift, -2.0)) in seams
    # The middle seam folds where it crosses the crease.
    assert ((3.0, 0.5 + lift, -1.0), (3.5, 0.75 + lift, -1.0)) in seams
    assert ((3.5, 0.75 + lift, -1.0), (4.0, 0.75 + lift, -1.0)) in seams


def test_deck_materials_show_the_ship_reflection() -> None:
    bridge = FakeJsBridge()
    reflection = ShipReflection(bridge)
    TrackMeshBuilder(bridge, NeonLines(bridge), reflection=reflection).build(
        make_level("N1 K1 .. .. .. .. .. ..").track
    )
    materials = bridge.three.MeshStandardMaterial.created
    assert len(materials) == 2
    assert all(callable(material.onBeforeCompile) for material in materials)


def test_kill_patches_are_outlined_where_they_meet_other_tiles() -> None:
    three, _, _, _ = build("N1 N1 N1 .. .. .. .. ..\nN1 K1 N2 .. .. .. .. ..\nN1 .. N1 .. .. .. .. ..")
    y = 0.5 + TrackMeshBuilder.LINE_LIFT
    outline = rails_of(three, TrackMeshBuilder.KILL_OUTLINE_COLOR, TrackMeshBuilder.KILL_OUTLINE_WIDTH)
    assert outline == {
        ((1.0, y, -2.0), (1.0, y, -4.0)),  # beside the level tile on its left
        ((1.0, y, -2.0), (2.0, y, -2.0)),  # behind it
        ((2.0, y, -2.0), (2.0, y, -4.0)),  # under the higher tile on its right
    }  # its front drops away: that edge keeps its brighter rail
    assert ((1.0, y, -4.0), (2.0, y, -4.0)) in rails_of(
        three, Palette.tile_color(TileType.NORMAL), TrackMeshBuilder.LINE_WIDTH
    )
    seams = rails_of(three, TrackMeshBuilder.SEAM_COLOR)
    assert not outline & seams
    assert Palette.tile_color(TileType.NORMAL) == TrackMeshBuilder.KILL_OUTLINE_COLOR  # the track border's colour
    assert TrackMeshBuilder.SEAM_WIDTH < TrackMeshBuilder.KILL_OUTLINE_WIDTH < TrackMeshBuilder.LINE_WIDTH


def test_neighbouring_kill_tiles_share_no_outline() -> None:
    three, _, _, _ = build("N1 K1 K1 N1 .. .. .. ..")
    y = 0.5 + TrackMeshBuilder.LINE_LIFT
    outline = rails_of(three, TrackMeshBuilder.KILL_OUTLINE_COLOR, TrackMeshBuilder.KILL_OUTLINE_WIDTH)
    assert ((1.0, y, 0.0), (1.0, y, -2.0)) in outline
    assert ((3.0, y, 0.0), (3.0, y, -2.0)) in outline
    assert ((2.0, y, 0.0), (2.0, y, -2.0)) not in outline


def test_kill_tiles_have_no_red_lines() -> None:
    three, _, _, _ = build("N1 K1 .. .. .. .. .. ..")
    colors = {material.args[0]["color"] for material in three.LineMaterial.created}
    assert Palette.tile_color(TileType.KILL) not in colors
    rails = rails_of(three, Palette.tile_color(TileType.NORMAL), TrackMeshBuilder.LINE_WIDTH)
    y = 0.5 + TrackMeshBuilder.LINE_LIFT
    assert ((2.0, y, 0.0), (2.0, y, -2.0)) in rails  # the kill tile's border rides with the normal rails
