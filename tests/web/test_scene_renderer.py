# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import random

import pytest

from synthride.core.game_event import GameEvent
from synthride.core.ship import Ship
from synthride.core.vector3 import Vector3
from synthride.web.neon_lines import NeonLines
from synthride.web.scene_renderer import SceneRenderer
from tests.web.fakes.fake_element import FakeElement
from tests.web.fakes.fake_js_bridge import FakeJsBridge


def make_renderer() -> tuple[FakeJsBridge, FakeElement, SceneRenderer]:
    bridge = FakeJsBridge()
    container = FakeElement("stage")
    return bridge, container, SceneRenderer(bridge, container, NeonLines(bridge), rng=random.Random(1))  # noqa: S311


def test_sets_up_canvas_and_bloom_pipeline() -> None:
    _, container, renderer = make_renderer()
    assert container.children == [renderer.renderer.domElement]
    assert renderer.renderer.setPixelRatio.calls == [(2,)]
    assert len(renderer.composer.addPass.calls) == 3


def test_bloom_threshold_ramps_softly() -> None:
    _, _, renderer = make_renderer()
    assert renderer.bloom.highPassUniforms.smoothWidth.value == SceneRenderer.BLOOM_SOFTNESS


def test_post_processing_target_is_multisampled() -> None:
    bridge, _, _ = make_renderer()
    target = bridge.three.EffectComposer.created[0].args[1]
    assert target.args[2]["samples"] == SceneRenderer.MSAA_SAMPLES


def test_resize_updates_line_resolution() -> None:
    bridge = FakeJsBridge()
    lines = NeonLines(bridge)
    line = lines.segments([0, 0, 0, 1, 1, 1], 0xFFFFFF, 2)
    SceneRenderer(bridge, FakeElement("stage"), lines)
    assert line.args[1].resolution.set.calls[-1] == (800, 400)


def test_resize_follows_window() -> None:
    bridge, _, renderer = make_renderer()
    bridge.window.innerWidth, bridge.window.innerHeight = 1000, 500
    bridge.window.dispatch("resize")
    assert renderer.renderer.setSize.calls[-1] == (1000, 500)
    assert renderer.camera.aspect == 2


def test_follow_snaps_behind_ship_and_widens_fov() -> None:
    _, _, renderer = make_renderer()
    ship = Ship(Vector3(4, 0.5, 10))
    renderer.follow(ship, speed_fraction=1.0, dt=0.016, snap=True)
    x, y, z = renderer.camera.position.set.calls[-1]
    assert (x, y) == pytest.approx((4, 0.5 + SceneRenderer.CAMERA_HEIGHT))
    assert z == pytest.approx(-10 + SceneRenderer.CAMERA_DISTANCE)
    assert renderer.camera_z == z
    assert renderer.camera.fov == SceneRenderer.BASE_FOV + SceneRenderer.SPEED_FOV


def test_follow_ducks_under_tunnel_roofs() -> None:
    _, _, renderer = make_renderer()
    renderer.follow(Ship(Vector3(4, 0.5, 10)), 0, 0.016, snap=True, ceiling=1.4)
    assert renderer.camera.position.set.calls[-1][1] == pytest.approx(1.4 - SceneRenderer.CEILING_MARGIN)
    renderer.follow(Ship(Vector3(4, 0.5, 10)), 0, 0.016, snap=True, ceiling=0.6)
    assert renderer.camera.position.set.calls[-1][1] == pytest.approx(0.5 + SceneRenderer.MIN_HEIGHT)


def test_follow_eases_sideways() -> None:
    _, _, renderer = make_renderer()
    renderer.follow(Ship(Vector3(0, 0, 0)), 0, 0.016, snap=True)
    renderer.follow(Ship(Vector3(2, 0, 0)), 0, 0.016)
    assert 0 < renderer.camera.position.set.calls[-1][0] < 2


def test_crash_shakes_camera() -> None:
    _, _, renderer = make_renderer()
    renderer.react([GameEvent.CRASHED])
    renderer.follow(Ship(Vector3(0, 0, 0)), 0, 0.016, snap=True)
    x = renderer.camera.position.set.calls[-1][0]
    assert x != 0


def test_add_remove_and_render() -> None:
    _, _, renderer = make_renderer()
    renderer.add("mesh")
    renderer.remove("mesh")
    renderer.render()
    assert renderer.scene.add.calls[-1] == ("mesh",)
    assert renderer.scene.remove.calls == [("mesh",)]
    assert renderer.composer.render.calls == [()]


def test_camera_never_rolls_when_strafing() -> None:
    _, _, renderer = make_renderer()
    renderer.follow(Ship(Vector3(4, 0.5, 10), velocity=Vector3(5, 0, 10)), 0.5, 0.016)
    assert renderer.camera.rotateZ.calls == []


def test_follow_places_the_reflection_on_the_deck_under_the_ship() -> None:
    _, _, renderer = make_renderer()
    ship = Ship(Vector3(4, 0.5 + 0.3, 10))
    renderer.follow(ship, 0, 0.016, snap=True)
    renderer.reflect_on(ship, 0.5)
    assert renderer.reflection.strength > 0
    renderer.render()
    eye = renderer.camera.position.set.calls[-1]
    assert renderer.reflection.camera.position.set.calls[-1] == pytest.approx((eye[0], 1.0 - eye[1], eye[2]))


def test_no_reflection_over_a_gap() -> None:
    _, _, renderer = make_renderer()
    renderer.reflect_on(Ship(Vector3(4, 0.5, 10)), None)
    assert renderer.reflection.strength == 0
