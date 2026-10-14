import pytest

from synthride.core.level_parser import LevelParser
from synthride.core.tile_type import TileType
from synthride.web.palette import Palette
from synthride.web.tile_decals import TileDecals
from tests.web.fakes.fake_js_bridge import FakeJsBridge


def build(*rows: str):
    bridge = FakeJsBridge()
    decals = TileDecals(bridge)
    group = decals.build(LevelParser().parse("---\n" + "\n".join(rows)).track)
    return bridge.three, decals, group


def test_every_special_tile_type_is_marked():
    assert set(TileDecals.DECKS) == set(TileType) - {TileType.NORMAL}


def test_one_layer_per_marked_tile_type_and_none_for_plain_tiles():
    three, decals, group = build("N1 B1 B1 K1 .. .. .. ..", "N1 B1 B1 K1 .. .. .. ..")
    assert decals.layer_count == 2
    assert len(group.add.calls) == 2
    colors = sorted(material.args[0]["color"] for material in three.MeshBasicMaterial.created)
    assert colors == sorted(Palette.tile_color(t) for t in (TileType.BOOST, TileType.KILL))
    boost_positions = three.BufferAttribute.created[0].args[0]
    assert len(boost_positions) == 4 * 6 * 3  # four tiles, two triangles each
    assert set(boost_positions[1::3]) == {0.5 + TileDecals.DECK_LIFT}


def test_uvs_follow_the_track_so_patterns_run_across_tiles():
    three, _, _ = build(".. B1 .. .. .. .. .. ..")
    uvs = three.BufferAttribute.created[1].args[0]
    assert set(uvs[0::2]) == {1.0, 2.0}
    assert set(uvs[1::2]) == {0.0, 1.0}


def test_jump_pads_raise_one_sheet_at_the_front_of_each_patch():
    three, decals, _ = build(*["J1 J1 .. .. .. .. .. .."] * 3)
    assert decals.layer_count == 2  # deck target and the rising arrows sheet
    sheet = three.BufferAttribute.created[3].args[0]
    assert len(sheet) == 2 * 6 * 3  # two tiles wide, only the first row
    assert set(sheet[2::3]) == {-0.5}
    assert max(sheet[1::3]) == pytest.approx(0.5 + TileDecals.CURTAIN_HEIGHT)


def test_animation_slides_the_pattern_along_its_drift():
    three, decals, _ = build(".. B1 .. .. .. .. .. ..")
    decals.animate(0.1)
    texture = three.CanvasTexture.created[0]
    dx, dy = TileDecals.DECKS[TileType.BOOST].drift
    assert texture.offset.set.calls[-1] == pytest.approx((-dx * 0.1 % 1, -dy * 0.1 % 1))


def test_pulsing_layers_throb_in_opacity():
    three, decals, _ = build(".. K1 .. .. .. .. .. ..")
    decals.animate(0.2)
    material = three.MeshBasicMaterial.created[0]
    assert 0 < material.opacity <= TileDecals.DECKS[TileType.KILL].opacity


def test_rebuilding_frees_the_old_textures():
    three, decals, _ = build(".. B1 .. .. .. .. .. ..")
    decals.build(LevelParser().parse("---\n" + "N1 " * 8).track)
    assert three.CanvasTexture.created[0].dispose.calls == [()]
    assert decals.layer_count == 0
