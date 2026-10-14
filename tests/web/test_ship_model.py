import math

import pytest

from synthride.core.game_phase import GamePhase
from synthride.core.ship import Ship
from synthride.core.vector3 import Vector3
from synthride.web.neon_lines import NeonLines
from synthride.web.ship_model import ShipModel
from tests.web.fakes.fake_js_bridge import FakeJsBridge


def make_model() -> ShipModel:
    bridge = FakeJsBridge()
    return ShipModel(bridge, NeonLines(bridge))


def test_outline_uses_thick_lines():
    bridge = FakeJsBridge()
    ShipModel(bridge, NeonLines(bridge))
    assert bridge.three.LineMaterial.created[0].args[0]["linewidth"] == ShipModel.LINE_WIDTH


def test_follows_ship_in_world_coordinates_and_banks():
    model = make_model()
    model.sync(Ship(Vector3(3, 1, 7), velocity=Vector3(2, 0, 5)), GamePhase.PLAYING, 0.016)
    assert model.group.position.set.calls[-1] == (3, 1, -7)
    assert model.body.rotation.z == pytest.approx(-2 * ShipModel.BANK_PER_SPEED)
    assert model.body.visible
    assert not model.explosion.visible


def test_explodes_while_dying():
    model = make_model()
    ship = Ship(Vector3())
    model.sync(ship, GamePhase.DYING, 0.5)
    assert not model.body.visible
    assert model.explosion.visible
    assert model.explosion.scale.setScalar.calls[-1] == (1 + 0.5 * ShipModel.EXPLOSION_GROWTH,)
    model.sync(ship, GamePhase.DYING, 0.6)
    model.sync(ship, GamePhase.PLAYING, 0.1)
    assert model.body.visible
    model.sync(ship, GamePhase.DYING, 0.1)
    assert model.explosion.scale.setScalar.calls[-1] == (1 + 0.1 * ShipModel.EXPLOSION_GROWTH,)


PARTS = (ShipModel.BODY, ShipModel.CANOPY, *ShipModel.RUNNERS, ShipModel.SPOILER, *ShipModel.STRUTS)


def test_every_part_is_a_triangle_soup():
    bridge = FakeJsBridge()
    ShipModel(bridge, NeonLines(bridge))
    expected = [ShipModel._lofted(rings) for rings in PARTS]
    positions = [attribute.args[0] for attribute in bridge.three.BufferAttribute.created]
    assert [len(p) for p in positions[: len(expected)]] == [len(triangles) * 3 for triangles in expected]


def test_lofted_skins_and_caps_rings():
    square = ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))
    raised = tuple((x, 1, z) for x, _, z in square)
    triangles = ShipModel._lofted((square, raised))
    assert len(triangles) == 3 * (4 * 2 + 4 * 2)


def test_sled_fits_inside_its_collision_box():
    points = [v for rings in PARTS for ring in rings for v in ring]
    assert max(abs(x) for x, _, _ in points) <= Ship.width / 2
    assert max(abs(z) for _, _, z in points) <= Ship.length / 2
    assert max(y for _, y, _ in points) <= Ship.height
    assert min(y for _, y, _ in points) == 0


def test_runners_rest_on_the_ground_under_the_body():
    for runner in ShipModel.RUNNERS:
        flat = [p for ring in runner[1:] for p in ring]
        assert min(y for _, y, _ in flat) == 0
        assert max(abs(x) for x, _, _ in flat) == pytest.approx(ShipModel.CONTACT_HALF_WIDTH)
    body_bottom = min(y for ring in ShipModel.BODY for _, y, _ in ring)
    runner_top = max(y for runner in ShipModel.RUNNERS for ring in runner[1:] for _, y, _ in ring)
    assert body_bottom == runner_top


def test_plume_stretches_with_speed():
    model = make_model()
    model.sync(Ship(Vector3(), velocity=Vector3(0, 0, 20)), GamePhase.PLAYING, 0.0)
    assert model.plume.scale.z == 2


def test_reactor_lights_span_the_whole_tail():
    bridge = FakeJsBridge()
    ShipModel(bridge, NeonLines(bridge))
    lights = bridge.three.PointLight.created
    xs = [light.position.set.calls[-1][0] for light in lights]
    assert len(lights) == len(ShipModel.REACTOR_LIGHTS_X)
    assert min(xs) < 0 < max(xs)


def test_contact_shadow_only_under_a_grounded_ship():
    model = make_model()
    model.sync(Ship(Vector3(), grounded=True), GamePhase.PLAYING, 0.016)
    assert model.shadow.visible
    model.sync(Ship(Vector3(), grounded=False), GamePhase.PLAYING, 0.016)
    assert not model.shadow.visible
    model.sync(Ship(Vector3(), grounded=True), GamePhase.DYING, 0.016)
    assert not model.shadow.visible


@pytest.mark.parametrize("strafe", [0.0, 1.5, -3.0])
def test_tilting_lifts_the_body_so_the_low_runner_stays_on_the_ground(strafe):
    model = make_model()
    model.sync(Ship(Vector3(), velocity=Vector3(strafe, 0, 10), grounded=True), GamePhase.PLAYING, 0.02)
    bank, pitch = model.body.rotation.z, model.body.rotation.x
    lowest_corner = (
        model.body.position.y
        - ShipModel.CONTACT_HALF_WIDTH * abs(math.sin(bank))
        - ShipModel.CONTACT_HALF_LENGTH * abs(math.sin(pitch))
    )
    assert lowest_corner == pytest.approx(0)
    assert abs(bank) == pytest.approx(abs(strafe) * ShipModel.GROUND_BANK_PER_SPEED)


def test_a_grounded_ship_rests_still():
    model = make_model()
    ship = Ship(Vector3(), velocity=Vector3(0, 0, 10), grounded=True)
    for _ in range(5):
        model.sync(ship, GamePhase.PLAYING, 0.013)
        assert model.body.rotation.x == 0
        assert model.body.position.y == 0
