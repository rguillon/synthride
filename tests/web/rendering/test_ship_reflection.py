# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from types import SimpleNamespace

import pytest

from synthride.web.rendering.ship_reflection import ShipReflection
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def make_reflection() -> tuple[FakeJsBridge, ShipReflection]:
    bridge = FakeJsBridge()
    return bridge, ShipReflection(bridge)


def compile_patched(reflection: ShipReflection) -> SimpleNamespace:
    """Compile a fake standard shader through a material patched by ``reflection``."""
    material = FakeJsObject("material")
    reflection.patch(material)
    shader = SimpleNamespace(
        uniforms=SimpleNamespace(),
        vertexShader="void main() {\n#include <project_vertex>\n}",
        fragmentShader="void main() {\n#include <opaque_fragment>\n}",
    )
    material.onBeforeCompile(shader, None)
    return shader


def test_mirror_camera_only_sees_the_reflection_layer() -> None:
    _, reflection = make_reflection()
    assert reflection.camera.layers.set.calls == [(ShipReflection.LAYER,)]


def test_include_puts_every_descendant_on_the_layer() -> None:
    _, reflection = make_reflection()
    item, child = FakeJsObject("ship"), FakeJsObject("hull")
    reflection.include(item)
    (visit,) = item.traverse.calls[0]
    visit(child)
    assert child.layers.enable.calls == [(ShipReflection.LAYER,)]


def test_resize_renders_at_reduced_resolution() -> None:
    _, reflection = make_reflection()
    reflection.resize(1000, 500)
    assert reflection.target.setSize.calls[-1] == (500, 250)


def test_patch_injects_reflection_into_the_standard_shader() -> None:
    _, reflection = make_reflection()
    shader = compile_patched(reflection)
    assert shader.uniforms.reflectionMap.args == (reflection.target.texture,)
    assert "vReflectWorld = " in shader.vertexShader
    assert shader.vertexShader.count("#include <project_vertex>") == 1
    assert "outgoingLight += reflected" in shader.fragmentShader
    assert shader.fragmentShader.count("#include <opaque_fragment>") == 1


def test_reflection_fades_as_the_ship_climbs_and_vanishes_over_gaps() -> None:
    _, reflection = make_reflection()
    reflection.place((0, 1.0, 0), 0.5)
    assert reflection.strength == ShipReflection.STRENGTH
    reflection.place((0, 0.5 + (ShipReflection.FADE_START + ShipReflection.FADE_END) / 2, 0), 0.5)
    assert reflection.strength == pytest.approx(ShipReflection.STRENGTH / 2)
    reflection.place((0, 10.0, 0), 0.5)
    assert reflection.strength == 0
    reflection.place((0, 1.0, 0), None)
    assert reflection.strength == 0


def test_render_mirrors_the_camera_through_the_deck() -> None:
    _, reflection = make_reflection()
    renderer, scene, camera = FakeJsObject("renderer"), FakeJsObject("scene"), FakeJsObject("camera")
    strength = compile_patched(reflection).uniforms.reflectionStrength
    reflection.place((2, 1.0, -5), 0.5)
    reflection.render(renderer, scene, camera, (2, 2.0, -1), (2, 1.3, -13))
    assert reflection.camera.position.set.calls[-1] == (2, -1.0, -1)
    assert reflection.camera.lookAt.calls[-1] == (2, pytest.approx(-0.3), -13)
    assert renderer.setRenderTarget.calls == [(reflection.target,)]
    assert renderer.render.calls == [(scene, reflection.camera)]
    assert strength.value == ShipReflection.STRENGTH


def test_render_skips_the_pass_when_nothing_shows() -> None:
    _, reflection = make_reflection()
    renderer = FakeJsObject("renderer")
    strength = compile_patched(reflection).uniforms.reflectionStrength
    reflection.place((0, 1.0, 0), None)
    reflection.render(renderer, FakeJsObject("scene"), FakeJsObject("camera"), (0, 1, 0), (0, 0, -1))
    assert renderer.render.calls == []
    assert strength.value == 0
