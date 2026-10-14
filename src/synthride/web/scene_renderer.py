from __future__ import annotations

import math
import random
from typing import Any

from synthride.core.game_event import GameEvent
from synthride.core.ship import Ship
from synthride.web.js_bridge import JsBridge
from synthride.web.neon_lines import NeonLines
from synthride.web.palette import Palette


class SceneRenderer:
    """Owns the Three.js renderer, scene, chase camera and bloom post-processing."""

    BASE_FOV = 68.0
    SPEED_FOV = 16.0
    CAMERA_HEIGHT = 1.25
    CAMERA_DISTANCE = 3.6
    LOOK_AHEAD = 8.0
    FOLLOW_RATE = 7.0
    MSAA_SAMPLES = 4
    SHAKE_EVENTS = frozenset({GameEvent.CRASHED, GameEvent.BURNED, GameEvent.FELL, GameEvent.NUDGED})

    def __init__(self, bridge: JsBridge, container: Any, lines: NeonLines, rng: random.Random | None = None) -> None:
        three, window = bridge.three, bridge.window
        self._bridge = bridge
        self._lines = lines
        self._rng = rng or random.Random()  # noqa: S311
        self.renderer = three.WebGLRenderer.new(bridge.obj(antialias=True, powerPreference="high-performance"))
        self.renderer.setPixelRatio(min(window.devicePixelRatio, 2))
        self.renderer.toneMapping = three.ACESFilmicToneMapping
        container.appendChild(self.renderer.domElement)
        self.scene = three.Scene.new()
        self.scene.fog = three.Fog.new(Palette.FOG, 30, 170)
        self.camera = three.PerspectiveCamera.new(self.BASE_FOV, 1, 0.1, 1500)
        self.scene.add(three.HemisphereLight.new(Palette.GRID, Palette.SHIP_EDGE, 0.25))
        sunlight = three.DirectionalLight.new(0xFFD1F0, 0.5)
        sunlight.position.set(4, 12, -20)
        self.scene.add(sunlight)
        # Post-processing renders off-screen, which bypasses the canvas antialiasing: multisample the target.
        target = three.WebGLRenderTarget.new(1, 1, bridge.obj(type=three.HalfFloatType, samples=self.MSAA_SAMPLES))
        self.composer = three.EffectComposer.new(self.renderer, target)
        self.composer.addPass(three.RenderPass.new(self.scene, self.camera))
        self.bloom = three.UnrealBloomPass.new(three.Vector2.new(1, 1), 0.7, 0.35, 0.55)
        self.composer.addPass(self.bloom)
        self.composer.addPass(three.OutputPass.new())
        self._camera_position = [0.0, 0.0, 0.0]
        self._shake = 0.0
        self.resize()
        window.addEventListener("resize", bridge.proxy(lambda _event: self.resize()))

    @property
    def camera_z(self) -> float:
        return self._camera_position[2]

    def resize(self) -> None:
        width, height = self._bridge.window.innerWidth, self._bridge.window.innerHeight
        self.renderer.setSize(width, height)
        self.composer.setSize(width, height)
        self.camera.aspect = width / max(height, 1)
        self.camera.updateProjectionMatrix()
        self._lines.resize(width, height)

    def add(self, item: Any) -> None:
        self.scene.add(item)

    def remove(self, item: Any) -> None:
        self.scene.remove(item)

    def react(self, events: list[GameEvent]) -> None:
        if any(event in self.SHAKE_EVENTS for event in events):
            self._shake = 0.15 if events == [GameEvent.NUDGED] else 0.5

    def follow(self, ship: Ship, speed_fraction: float, dt: float, snap: bool = False) -> None:
        """Eases the chase camera toward its spot behind the ship and widens the view with speed."""
        x, y, z = ship.position.x, ship.position.y, -ship.position.z
        target = (x, y + self.CAMERA_HEIGHT, z + self.CAMERA_DISTANCE)
        blend = 1.0 if snap else 1 - math.exp(-self.FOLLOW_RATE * dt)
        self._camera_position = [
            current + (goal - current) * blend for current, goal in zip(self._camera_position, target, strict=True)
        ]
        self._camera_position[2] = target[2]  # never lag behind along the track
        self._shake *= math.exp(-6 * dt)
        jitter = [self._rng.uniform(-self._shake, self._shake) for _ in range(2)]
        cx, cy, cz = self._camera_position
        self.camera.position.set(cx + jitter[0], cy + jitter[1], cz)
        self.camera.lookAt(x, y + 0.3, z - self.LOOK_AHEAD)
        self.camera.fov = self.BASE_FOV + self.SPEED_FOV * speed_fraction
        self.camera.updateProjectionMatrix()

    def render(self) -> None:
        self.composer.render()
