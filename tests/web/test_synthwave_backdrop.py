from synthride.web.neon_lines import NeonLines
from synthride.web.synthwave_backdrop import SynthwaveBackdrop
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def make_backdrop() -> SynthwaveBackdrop:
    bridge = FakeJsBridge()
    return SynthwaveBackdrop(bridge, NeonLines(bridge))


def test_grid_spans_its_size_in_cells():
    positions = SynthwaveBackdrop.grid_positions()
    lines_per_axis = int(SynthwaveBackdrop.GRID_SIZE / SynthwaveBackdrop.GRID_CELL) + 1
    assert len(positions) == lines_per_axis * 2 * 6
    assert max(positions) == SynthwaveBackdrop.GRID_SIZE / 2
    assert set(positions[1::3]) == {0}


def test_adds_sky_group_and_grid_to_scene():
    backdrop = make_backdrop()
    scene = FakeJsObject("scene")
    backdrop.add_to(scene)
    assert scene.add.calls == [(backdrop.group,), (backdrop.grid,)]
    assert len(backdrop.group.add.calls) == 3


def test_stars_are_deterministic():
    first, second = FakeJsBridge(), FakeJsBridge()
    SynthwaveBackdrop(first, NeonLines(first), seed=3)
    SynthwaveBackdrop(second, NeonLines(second), seed=3)
    stars = first.three.BufferAttribute.created[0].args[0]
    assert len(stars) == SynthwaveBackdrop.STAR_COUNT * 3
    assert stars == second.three.BufferAttribute.created[0].args[0]


def test_update_follows_camera_and_snaps_grid_to_cells():
    backdrop = make_backdrop()
    backdrop.update(camera_z=-12.0, time=4.0)
    assert backdrop.group.position.z == -12.0
    assert backdrop.grid.position.z == -15.0
    assert backdrop.grid.position.y == SynthwaveBackdrop.GRID_DEPTH
