# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Deep space around the track."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from synthride.web.rendering.palette import Palette
from synthride.web.rendering.space_scenery import SpaceScenery

if TYPE_CHECKING:
    from synthride.web.browser.js_bridge import JsBridge, JsObject


class SpaceBackdrop:
    """Deep space: a nebula-streaked sky dome, a planet and maybe a moon, a twinkling starfield and drifting dust.

    The sky, planet, moon and stars ride along with the camera, so they look infinitely far away. The dust
    is wrapped around the camera in its vertex shader, so it streams past forever and shows speed. Each level
    dresses the sky in its own :class:`SpaceScenery`, by changing shader uniforms only.
    """

    STAR_COUNT = 1400
    STAR_RADIUS = 480.0
    DUST_COUNT = 900
    DUST_DEPTH = 160.0  # the length of the dust field, wrapped around the camera
    DUST_AHEAD = 20.0  # how far behind the camera the field reaches
    DUST_SPREAD = ((-30.0, 38.0), (-14.0, 16.0))  # x and y ranges, around the eight-tile-wide track
    PLANET_SIZE = 150.0  # the planet's quad; each scenery scales it to its own size
    NOISE = """
        float hash(vec3 p) {
            p = fract(p * 0.3183099 + 0.1);
            p *= 17.0;
            return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
        }
        float noise(vec3 x) {
            vec3 i = floor(x);
            vec3 f = fract(x);
            f = f * f * (3.0 - 2.0 * f);
            return mix(
                mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x),
                    mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
                mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x),
                    mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y),
                f.z);
        }
        float fbm(vec3 p) {
            float value = 0.0;
            float amplitude = 0.5;
            for (int i = 0; i < 5; i++) {
                value += amplitude * noise(p);
                p = p * 2.03 + vec3(1.7, 9.2, 3.1);
                amplitude *= 0.5;
            }
            return value;
        }
    """
    SKY_VERTEX = """
        varying vec3 vWorld;
        void main() {
            vWorld = (modelMatrix * vec4(position, 1.0)).xyz;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    """
    SKY_FRAGMENT = (
        """
        varying vec3 vWorld;
        uniform vec3 uSpace;
        uniform vec3 uNebula;
        uniform vec3 uNebulaGlow;
        uniform vec3 uBandAxis;
        uniform vec3 uSkyOffset;
    """
        + NOISE
        + """
        void main() {
            vec3 d = normalize(vWorld - cameraPosition);
            float tilt = dot(d, uBandAxis) / 0.3;
            float band = exp(-tilt * tilt);
            float clouds = fbm(d * 2.6 + uSkyOffset);
            float wisps = fbm(d * 6.5 + clouds * 2.5 + uSkyOffset);
            vec3 color = uSpace;
            color += uNebula * smoothstep(0.42, 0.85, clouds) * 0.35;
            color += uNebulaGlow * smoothstep(0.5, 0.9, wisps) * band * 0.22;
            color += vec3(0.35, 0.3, 0.5) * band * wisps * 0.05;
            gl_FragColor = vec4(color, 1.0);
        }
    """
    )
    PLANET_VERTEX = """
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    """
    PLANET_FRAGMENT = (
        """
        varying vec2 vUv;
        uniform vec3 uDark;
        uniform vec3 uLight;
        uniform vec3 uRim;
        uniform vec3 uSun;
        uniform vec3 uSeed;
        uniform float uBands;
        uniform float uMottle;
        uniform float uRing;
        const float RADIUS = 0.5;
    """
        + NOISE
        + """
        void main() {
            vec2 p = (vUv - 0.5) * 2.0;
            vec2 tilted = vec2(p.x * 0.94 + p.y * 0.34, -p.x * 0.34 + p.y * 0.94);
            float ringRadius = length(vec2(tilted.x, tilted.y * 4.2));
            float ring = smoothstep(0.62, 0.66, ringRadius) * (1.0 - smoothstep(0.9, 0.95, ringRadius))
                * (0.55 + 0.45 * sin(ringRadius * 70.0)) * uRing;
            vec3 ringColor = mix(uLight, uRim, 0.3) * 0.35;
            float r = length(p) / RADIUS;
            vec4 color = vec4(0.0);
            if (r < 1.0) {
                vec3 n = vec3(p / RADIUS, sqrt(1.0 - r * r));
                float light = clamp(dot(n, uSun), 0.0, 1.0);
                float bands = 0.5 + 0.5 * sin(n.y * uBands + sin(n.x * 4.0) * 1.4);
                bands = mix(bands, smoothstep(0.25, 0.75, fbm(n * 3.5 + uSeed)), uMottle);
                vec3 surface = mix(uDark, uLight, bands) * (0.04 + 0.5 * light);
                surface += uRim * pow(1.0 - n.z, 3.0) * light * 0.4;
                color = vec4(surface, 1.0);
                if (tilted.y < 0.0) color.rgb = mix(color.rgb, ringColor, ring * 0.85);
            } else if (ring > 0.01) {
                color = vec4(ringColor, ring * 0.8);
            } else {
                color = vec4(uRim * 0.5, exp(-(r - 1.0) * 18.0) * 0.4);
            }
            if (color.a < 0.004) discard;
            gl_FragColor = color;
        }
    """
    )
    STAR_VERTEX = """
        attribute float aSize;
        attribute float aPhase;
        attribute vec3 aColor;
        uniform float uTime;
        uniform float uPixelRatio;
        varying vec3 vColor;
        void main() {
            float twinkle = 0.6 + 0.4 * sin(uTime * (1.0 + aPhase * 2.5) + aPhase * 40.0);
            vColor = aColor * twinkle;
            gl_PointSize = aSize * uPixelRatio;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    """
    STAR_FRAGMENT = """
        varying vec3 vColor;
        void main() {
            float d = length(gl_PointCoord - 0.5);
            if (d > 0.5) discard;
            gl_FragColor = vec4(vColor * (1.0 - smoothstep(0.0, 0.5, d)), 1.0);
        }
    """
    DUST_VERTEX = """
        attribute float aSize;
        uniform float uCameraZ;
        uniform float uDepth;
        uniform float uAhead;
        uniform float uPixelRatio;
        varying float vFade;
        void main() {
            vec3 p = position;
            float front = uCameraZ + uAhead;
            p.z = front - mod(front - p.z, uDepth);
            vec4 view = modelViewMatrix * vec4(p, 1.0);
            float distance = -view.z;
            vFade = (1.0 - smoothstep(40.0, uDepth - uAhead, distance)) * smoothstep(0.5, 4.0, distance);
            gl_PointSize = clamp(aSize * uPixelRatio * 40.0 / max(distance, 0.1), 1.0, 12.0);
            gl_Position = projectionMatrix * view;
        }
    """
    DUST_FRAGMENT = """
        uniform vec3 uColor;
        varying float vFade;
        void main() {
            float d = length(gl_PointCoord - 0.5);
            if (d > 0.5) discard;
            gl_FragColor = vec4(uColor * vFade * (1.0 - smoothstep(0.0, 0.5, d)) * 0.6, 1.0);
        }
    """

    def __init__(self, bridge: JsBridge, seed: int = 1984) -> None:
        """Build the sky, planet, moon, stars and dust, scattered from ``seed``, in the first level's scenery."""
        self._bridge = bridge
        three = bridge.three
        rng = random.Random(seed)  # noqa: S311
        self._pixel_ratio = min(bridge.window.devicePixelRatio, 2)
        self.group = three.Group.new()
        self.stars = self._make_stars(rng)
        self.dust = self._make_dust(rng)
        self._sky_material = self._shader(
            self.SKY_VERTEX,
            self.SKY_FRAGMENT,
            {"uSpace": Palette.SPACE, "uNebula": Palette.NEBULA, "uNebulaGlow": Palette.NEBULA_GLOW},
            ("uBandAxis", "uSkyOffset"),
            side=three.BackSide,
        )
        sky = three.Mesh.new(three.SphereGeometry.new(600, 32, 20), self._sky_material)
        self.planet, self._planet_material = self._make_planet(self.PLANET_SIZE)
        self.moon, self._moon_material = self._make_planet(1.0)
        # Painted back to front: sky, then stars, then the planet over them and the nearer moon over it.
        for order, part in enumerate((sky, self.stars, self.planet, self.moon)):
            part.renderOrder = order - 4
            self.group.add(part)
        self.show(SpaceScenery.for_level(0))

    def show(self, scenery: SpaceScenery) -> None:
        """Dress the sky in ``scenery``."""
        theme = scenery.theme
        sky = self._sky_material.uniforms
        sky.uSpace.value.setHex(theme.space)
        sky.uNebula.value.setHex(theme.nebula)
        sky.uNebulaGlow.value.setHex(theme.nebula_glow)
        sky.uBandAxis.value.set(*scenery.band_axis)
        sky.uSkyOffset.value.set(*scenery.sky_offset)
        planet = self._planet_material.uniforms
        planet.uDark.value.setHex(theme.planet_dark)
        planet.uLight.value.setHex(theme.planet_light)
        planet.uRim.value.setHex(theme.planet_rim)
        planet.uSun.value.set(*scenery.sun)
        planet.uSeed.value.set(*scenery.sky_offset)
        planet.uBands.value = scenery.bands
        planet.uMottle.value = scenery.mottle
        planet.uRing.value = 1.0 if scenery.ring else 0.0
        self._place(self.planet, scenery.planet_position, scenery.planet_size / self.PLANET_SIZE)
        # The moon is a small, ringless, cratered rock lit like the planet, in the theme's light colours.
        moon = self._moon_material.uniforms
        moon.uDark.value.setHex(theme.planet_dark)
        moon.uLight.value.setHex(theme.planet_rim)
        moon.uRim.value.setHex(theme.planet_light)
        moon.uSun.value.set(*scenery.sun)
        moon.uSeed.value.set(*scenery.band_axis)
        moon.uBands.value = 3.0
        moon.uMottle.value = 0.9
        moon.uRing.value = 0.0
        self.moon.visible = scenery.moon_size > 0
        self._place(self.moon, scenery.moon_position, max(scenery.moon_size, 1.0))

    def _place(self, mesh: JsObject, position: tuple[float, float, float], scale: float) -> None:
        """Put ``mesh`` at ``position`` in the sky, facing its centre: the group's origin, wherever it has moved."""
        mesh.position.set(*position)
        mesh.scale.setScalar(scale)
        mesh.lookAt(0, 0, self.group.position.z)

    def _make_planet(self, size: float) -> tuple[JsObject, JsObject]:
        three = self._bridge.three
        material = self._shader(
            self.PLANET_VERTEX,
            self.PLANET_FRAGMENT,
            {"uDark": Palette.PLANET_DARK, "uLight": Palette.PLANET_LIGHT, "uRim": Palette.PLANET_RIM},
            ("uSun", "uSeed"),
            ("uBands", "uMottle", "uRing"),
            transparent=True,
        )
        return three.Mesh.new(three.PlaneGeometry.new(size, size), material), material

    def _shader(
        self,
        vertex: str,
        fragment: str,
        colors: dict[str, int],
        vectors: tuple[str, ...] = (),
        scalars: tuple[str, ...] = (),
        **options: object,
    ) -> JsObject:
        three = self._bridge.three
        uniforms: dict[str, dict[str, object]] = {
            name: {"value": three.Color.new(color)} for name, color in colors.items()
        }
        uniforms |= {name: {"value": three.Vector3.new()} for name in vectors}
        uniforms |= {name: {"value": 0.0} for name in scalars}
        return three.ShaderMaterial.new(
            self._bridge.obj(
                uniforms=uniforms,
                vertexShader=vertex,
                fragmentShader=fragment,
                depthWrite=False,
                fog=False,
                **options,
            )
        )

    def star_positions(self, rng: random.Random) -> list[float]:
        """Return stars spread evenly over a sphere around the origin, as x, y, z triples."""
        positions: list[float] = []
        for _ in range(self.STAR_COUNT):
            y = rng.uniform(-1.0, 1.0)
            angle = rng.uniform(0.0, 2 * math.pi)
            ring = math.sqrt(1 - y * y)
            positions += [math.cos(angle) * ring, y, math.sin(angle) * ring]
        return [coordinate * self.STAR_RADIUS for coordinate in positions]

    def _make_stars(self, rng: random.Random) -> JsObject:
        three = self._bridge.three
        positions = self.star_positions(rng)
        sizes, phases, colors = [], [], []
        for _ in range(self.STAR_COUNT):
            sizes.append(1.0 + 2.6 * rng.random() ** 4)  # mostly faint pin-pricks, a few bright stars
            phases.append(rng.random())
            brightness = 0.35 + 0.65 * rng.random() ** 2
            colors += [channel * brightness for channel in Palette.linear_rgb(rng.choice(Palette.STARS))]
        geometry = self._points_geometry(positions, aSize=sizes, aPhase=phases)
        geometry.setAttribute("aColor", three.BufferAttribute.new(self._bridge.float32_array(colors), 3))
        material = three.ShaderMaterial.new(
            self._bridge.obj(
                uniforms={"uTime": {"value": 0.0}, "uPixelRatio": {"value": self._pixel_ratio}},
                vertexShader=self.STAR_VERTEX,
                fragmentShader=self.STAR_FRAGMENT,
                blending=three.AdditiveBlending,
                transparent=True,
                depthWrite=False,
                fog=False,
            )
        )
        return three.Points.new(geometry, material)

    def _make_dust(self, rng: random.Random) -> JsObject:
        three = self._bridge.three
        (x0, x1), (y0, y1) = self.DUST_SPREAD
        positions: list[float] = []
        for _ in range(self.DUST_COUNT):
            positions += [rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(-self.DUST_DEPTH, 0.0)]
        sizes = [0.5 + rng.random() for _ in range(self.DUST_COUNT)]
        material = three.ShaderMaterial.new(
            self._bridge.obj(
                uniforms={
                    "uCameraZ": {"value": 0.0},
                    "uDepth": {"value": self.DUST_DEPTH},
                    "uAhead": {"value": self.DUST_AHEAD},
                    "uPixelRatio": {"value": self._pixel_ratio},
                    "uColor": {"value": three.Color.new(Palette.DUST)},
                },
                vertexShader=self.DUST_VERTEX,
                fragmentShader=self.DUST_FRAGMENT,
                blending=three.AdditiveBlending,
                transparent=True,
                depthWrite=False,
                fog=False,
            )
        )
        dust = three.Points.new(self._points_geometry(positions, aSize=sizes), material)
        dust.frustumCulled = False  # the shader moves every particle away from where the geometry says
        return dust

    def _points_geometry(self, positions: list[float], **scalars: list[float]) -> JsObject:
        three, bridge = self._bridge.three, self._bridge
        geometry = three.BufferGeometry.new()
        geometry.setAttribute("position", three.BufferAttribute.new(bridge.float32_array(positions), 3))
        for name, values in scalars.items():
            geometry.setAttribute(name, three.BufferAttribute.new(bridge.float32_array(values), 1))
        return geometry

    def add_to(self, scene: JsObject) -> None:
        """Add the backdrop to ``scene``."""
        scene.add(self.group)
        scene.add(self.dust)

    def update(self, camera_z: float, time: float) -> None:
        """Keep the sky centred on the camera, stream the dust past it and twinkle the stars."""
        self.group.position.z = camera_z
        self.dust.material.uniforms.uCameraZ.value = camera_z
        self.stars.material.uniforms.uTime.value = time
