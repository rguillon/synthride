from __future__ import annotations

import random
from typing import Any

from synthride.web.js_bridge import JsBridge
from synthride.web.neon_lines import NeonLines
from synthride.web.palette import Palette


class SynthwaveBackdrop:
    """The retro sky: gradient dome, striped sun, starfield and an endless neon grid below the track."""

    GRID_CELL = 5.0
    GRID_DEPTH = -6.0
    GRID_SIZE = 800.0
    GRID_LINE_WIDTH = 1.5
    STAR_COUNT = 600
    SKY_VERTEX = """
        varying vec3 vWorld;
        void main() {
            vWorld = (modelMatrix * vec4(position, 1.0)).xyz;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    """
    SKY_FRAGMENT = """
        varying vec3 vWorld;
        uniform vec3 uTop;
        uniform vec3 uHorizon;
        void main() {
            float h = clamp(normalize(vWorld - cameraPosition).y * 2.5, 0.0, 1.0);
            gl_FragColor = vec4(mix(uHorizon, uTop, pow(h, 0.6)), 1.0);
        }
    """
    SUN_VERTEX = """
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    """
    SUN_FRAGMENT = """
        varying vec2 vUv;
        uniform float uTime;
        void main() {
            vec2 c = vUv - 0.5;
            if (length(c) > 0.5) discard;
            float y = vUv.y;
            if (y < 0.6) {
                float band = fract((y - uTime * 0.03) * 11.0);
                if (band < (0.6 - y) * 1.5) discard;
            }
            vec3 color = mix(vec3(0.85, 0.05, 0.45), vec3(1.0, 0.8, 0.2), smoothstep(0.15, 0.95, y));
            gl_FragColor = vec4(color, 1.0);
        }
    """

    def __init__(self, bridge: JsBridge, lines: NeonLines, seed: int = 1984) -> None:
        three = bridge.three
        self.group = three.Group.new()
        sky_uniforms = {
            "uTop": {"value": three.Color.new(Palette.NIGHT)},
            "uHorizon": {"value": three.Color.new(Palette.HORIZON)},
        }
        sky = three.Mesh.new(
            three.SphereGeometry.new(600, 24, 16),
            three.ShaderMaterial.new(
                bridge.obj(
                    uniforms=sky_uniforms,
                    vertexShader=self.SKY_VERTEX,
                    fragmentShader=self.SKY_FRAGMENT,
                    side=three.BackSide,
                    depthWrite=False,
                    fog=False,
                )
            ),
        )
        self._sun_material = three.ShaderMaterial.new(
            bridge.obj(
                uniforms={"uTime": {"value": 0.0}},
                vertexShader=self.SUN_VERTEX,
                fragmentShader=self.SUN_FRAGMENT,
                transparent=True,
                depthWrite=False,
                fog=False,
            )
        )
        sun = three.Mesh.new(three.PlaneGeometry.new(160, 160), self._sun_material)
        sun.position.set(4, 22, -450)
        self._stars = self._make_stars(bridge, random.Random(seed))  # noqa: S311
        self.grid = lines.segments(self.grid_positions(), Palette.GRID, self.GRID_LINE_WIDTH)
        self.grid.position.y = self.GRID_DEPTH
        for part in (sky, sun, self._stars):
            self.group.add(part)

    @classmethod
    def grid_positions(cls) -> list[float]:
        """A square grid on the y=0 plane, centred on the origin, as line segment end points."""
        half = cls.GRID_SIZE / 2
        positions: list[float] = []
        for index in range(int(cls.GRID_SIZE / cls.GRID_CELL) + 1):
            offset = -half + index * cls.GRID_CELL
            positions += [offset, 0, -half, offset, 0, half]
            positions += [-half, 0, offset, half, 0, offset]
        return positions

    def _make_stars(self, bridge: JsBridge, rng: random.Random) -> Any:
        three = bridge.three
        positions = []
        for _ in range(self.STAR_COUNT):
            positions += [rng.uniform(-500, 500), rng.uniform(40, 380), rng.uniform(-560, -200)]
        geometry = three.BufferGeometry.new()
        geometry.setAttribute("position", three.BufferAttribute.new(bridge.float32_array(positions), 3))
        material = three.PointsMaterial.new(bridge.obj(color=0x9FA8FF, size=1.2, sizeAttenuation=False, fog=False))
        return three.Points.new(geometry, material)

    def add_to(self, scene: Any) -> None:
        scene.add(self.group)
        scene.add(self.grid)

    def update(self, camera_z: float, time: float) -> None:
        """Keeps the sky centred on the camera and slides the grid so it looks infinite."""
        self.group.position.z = camera_z
        self.grid.position.z = camera_z - camera_z % self.GRID_CELL
        self._sun_material.uniforms.uTime.value = time
