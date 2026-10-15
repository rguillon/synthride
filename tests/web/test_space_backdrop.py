# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import math
import random

from synthride.web.space_backdrop import SpaceBackdrop
from synthride.web.space_scenery import SpaceScenery
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def make_backdrop(seed: int = 1984) -> tuple[FakeJsBridge, SpaceBackdrop]:
    bridge = FakeJsBridge()
    return bridge, SpaceBackdrop(bridge, seed=seed)


def test_stars_surround_the_camera_on_a_sphere() -> None:
    _, backdrop = make_backdrop()
    positions = backdrop.star_positions(random.Random(1))
    assert len(positions) == SpaceBackdrop.STAR_COUNT * 3
    for index in range(0, len(positions), 3):
        x, y, z = positions[index : index + 3]
        assert math.isclose(math.sqrt(x * x + y * y + z * z), SpaceBackdrop.STAR_RADIUS)
    assert min(positions[1::3]) < 0 < max(positions[1::3])  # below the track too: there is no ground in space


def test_has_no_sun() -> None:
    bridge, _ = make_backdrop()
    assert len(bridge.three.PlaneGeometry.created) == 2  # the planet and its moon only


def test_adds_sky_group_and_dust_to_scene() -> None:
    _, backdrop = make_backdrop()
    scene = FakeJsObject("scene")
    backdrop.add_to(scene)
    assert scene.add.calls == [(backdrop.group,), (backdrop.dust,)]
    assert len(backdrop.group.add.calls) == 4  # sky, stars, planet, moon
    assert backdrop.dust.frustumCulled is False


def test_scattering_is_deterministic() -> None:
    first, _ = make_backdrop(seed=3)
    second, _ = make_backdrop(seed=3)
    attributes = [attribute.args[0] for attribute in first.three.BufferAttribute.created]
    assert attributes == [attribute.args[0] for attribute in second.three.BufferAttribute.created]


def test_update_follows_camera_streams_dust_and_twinkles() -> None:
    _, backdrop = make_backdrop()
    backdrop.update(camera_z=-12.0, time=4.0)
    assert backdrop.group.position.z == -12.0
    assert backdrop.dust.material.uniforms.uCameraZ.value == -12.0
    assert backdrop.stars.material.uniforms.uTime.value == 4.0


def test_show_dresses_the_sky_in_a_scenery() -> None:
    _, backdrop = make_backdrop()
    scenery = SpaceScenery.for_level(5)
    backdrop.show(scenery)
    sky, planet = backdrop._sky_material.uniforms, backdrop._planet_material.uniforms  # noqa: SLF001
    assert sky.uNebula.value.setHex.calls[-1] == (scenery.theme.nebula,)
    assert sky.uBandAxis.value.set.calls[-1] == scenery.band_axis
    assert planet.uLight.value.setHex.calls[-1] == (scenery.theme.planet_light,)
    assert planet.uBands.value == scenery.bands
    assert planet.uRing.value == (1.0 if scenery.ring else 0.0)
    assert backdrop.planet.position.set.calls[-1] == scenery.planet_position
    assert backdrop.planet.scale.setScalar.calls[-1] == (scenery.planet_size / SpaceBackdrop.PLANET_SIZE,)


def test_show_hides_the_moon_of_a_moonless_scenery() -> None:
    _, backdrop = make_backdrop()
    moonless = next(s for s in map(SpaceScenery.for_level, range(50)) if not s.moon_size)
    mooned = next(s for s in map(SpaceScenery.for_level, range(50)) if s.moon_size)
    backdrop.show(moonless)
    assert backdrop.moon.visible is False
    backdrop.show(mooned)
    assert backdrop.moon.visible is True
    assert backdrop.moon.scale.setScalar.calls[-1] == (mooned.moon_size,)
