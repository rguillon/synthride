# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The Three.js scene, chase camera and post-processing."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from synthride.core.game_event import GameEvent
from synthride.web.palette import Palette
from synthride.web.ship_reflection import ShipReflection

if TYPE_CHECKING:
    from synthride.core.ship import Ship
    from synthride.web.js_bridge import JsBridge, JsObject
    from synthride.web.neon_lines import NeonLines


class SceneRenderer:
    """Owns the Three.js renderer, scene, chase camera and bloom post-processing."""

    BASE_FOV = 68.0
    SPEED_FOV = 16.0
    CAMERA_HEIGHT = 1.25
    CAMERA_DISTANCE = 3.6
    LOOK_AHEAD = 8.0
    CEILING_MARGIN = 0.22  # how far under a tunnel roof the camera stays
    MIN_HEIGHT = 0.35
    EDITOR_HEIGHT = 7.0
    EDITOR_DISTANCE = 8.0
    EDITOR_LOOK_AHEAD = 12.0
    FOLLOW_RATE = 7.0
    MSAA_SAMPLES = 4
    FOG_NEAR = 30.0
    FOG_FAR = 170.0
    BLOOM_STRENGTH = 0.7
    BLOOM_RADIUS = 0.35
    # Bloom picks bright pixels at half resolution, so a thin line's brightness there depends on how it sits on
    # the pixel rows. A hard threshold turns that into glow popping on and off as lines move: ramp it softly.
    BLOOM_THRESHOLD = 0.35
    BLOOM_SOFTNESS = 0.5
    SHAKE_EVENTS = frozenset({GameEvent.CRASHED, GameEvent.BURNED, GameEvent.FELL, GameEvent.NUDGED, GameEvent.BUMPED})
    LIGHT_SHAKES = frozenset({GameEvent.NUDGED, GameEvent.BUMPED})

    def __init__(
        self,
        bridge: JsBridge,
        container: JsObject,
        lines: NeonLines,
        rng: random.Random | None = None,
        reflection: ShipReflection | None = None,
    ) -> None:
        """Create the renderer inside ``container`` and keep it sized to the window."""
        three, window = bridge.three, bridge.window
        self._bridge = bridge
        self._lines = lines
        self.reflection = reflection or ShipReflection(bridge)
        self._rng = rng or random.Random()  # noqa: S311
        self.renderer = three.WebGLRenderer.new(bridge.obj(antialias=True, powerPreference="high-performance"))
        self.renderer.setPixelRatio(min(window.devicePixelRatio, 2))
        self.renderer.toneMapping = three.ACESFilmicToneMapping
        container.appendChild(self.renderer.domElement)
        self.scene = three.Scene.new()
        self.scene.fog = three.Fog.new(Palette.FOG, self.FOG_NEAR, self.FOG_FAR)
        self.camera = three.PerspectiveCamera.new(self.BASE_FOV, 1, 0.1, 1500)
        skylight = three.HemisphereLight.new(Palette.GRID, Palette.SHIP_EDGE, 0.25)
        starlight = three.DirectionalLight.new(0xC9D2FF, 0.45)
        starlight.position.set(-6, 12, -20)
        for light in (skylight, starlight):
            self.scene.add(light)
            self.reflection.include(light)  # the mirrored ship needs the same lighting
        # Post-processing renders off-screen, which bypasses the canvas antialiasing: multisample the target.
        target = three.WebGLRenderTarget.new(1, 1, bridge.obj(type=three.HalfFloatType, samples=self.MSAA_SAMPLES))
        self.composer = three.EffectComposer.new(self.renderer, target)
        self.composer.addPass(three.RenderPass.new(self.scene, self.camera))
        self.bloom = three.UnrealBloomPass.new(
            three.Vector2.new(1, 1), self.BLOOM_STRENGTH, self.BLOOM_RADIUS, self.BLOOM_THRESHOLD
        )
        self.bloom.highPassUniforms.smoothWidth.value = self.BLOOM_SOFTNESS
        self.composer.addPass(self.bloom)
        self.composer.addPass(three.OutputPass.new())
        self._camera_position = [0.0, 0.0, 0.0]
        self._ground = 0.0  # the height the ship last stood at: the camera never sinks below it
        self._eye = (0.0, 0.0, 0.0)
        self._look = (0.0, 0.0, -1.0)
        self._shake = 0.0
        self.resize()
        window.addEventListener("resize", bridge.proxy(lambda _event: self.resize()))

    @property
    def camera_z(self) -> float:
        """The camera's position along the z axis."""
        return self._camera_position[2]

    def resize(self) -> None:
        """Fit the renderer and camera to the window."""
        width, height = self._bridge.window.innerWidth, self._bridge.window.innerHeight
        self.renderer.setSize(width, height)
        self.composer.setSize(width, height)
        self.reflection.resize(width, height)
        self.camera.aspect = width / max(height, 1)
        self.camera.updateProjectionMatrix()
        self._lines.resize(width, height)

    def add(self, item: JsObject) -> None:
        """Add ``item`` to the scene."""
        self.scene.add(item)

    def mirror(self, *items: JsObject) -> None:
        """Reflect ``items``, already in the scene, in the deck under the ship."""
        for item in items:
            self.reflection.include(item)

    def remove(self, item: JsObject) -> None:
        """Remove ``item`` from the scene."""
        self.scene.remove(item)

    def react(self, events: list[GameEvent]) -> None:
        """Shake the camera on impacts."""
        if any(event in self.SHAKE_EVENTS for event in events):
            hard = any(event in self.SHAKE_EVENTS - self.LIGHT_SHAKES for event in events)
            self._shake = 0.5 if hard else 0.15

    def follow(
        self, ship: Ship, speed_fraction: float, dt: float, *, snap: bool = False, ceiling: float | None = None
    ) -> None:
        """Eases the chase camera toward its spot behind the ship and widens the view with speed.

        Under a ``ceiling`` (a tunnel roof), the camera drops below it so the roof never hides the ship. While the
        ship is airborne the camera stays level with the ground it left, so a fall never shows the track from under.
        """
        x, y, z = ship.position.x, ship.position.y, -ship.position.z
        if ship.grounded or snap:
            self._ground = y
        height = max(y, self._ground) + self.CAMERA_HEIGHT
        if ceiling is not None:
            height = max(y + self.MIN_HEIGHT, min(height, ceiling - self.CEILING_MARGIN))
        target = (x, height, z + self.CAMERA_DISTANCE)
        blend = 1.0 if snap else 1 - math.exp(-self.FOLLOW_RATE * dt)
        self._camera_position = [
            current + (goal - current) * blend for current, goal in zip(self._camera_position, target, strict=True)
        ]
        self._camera_position[2] = target[2]  # never lag behind along the track
        self._shake *= math.exp(-6 * dt)
        jitter = [self._rng.uniform(-self._shake, self._shake) for _ in range(2)]
        cx, cy, cz = self._camera_position
        self._eye = (cx + jitter[0], cy + jitter[1], cz)
        self._look = (x, y + 0.3, z - self.LOOK_AHEAD)
        self.camera.position.set(*self._eye)
        self.camera.lookAt(*self._look)
        self.camera.fov = self.BASE_FOV + self.SPEED_FOV * speed_fraction
        self.camera.updateProjectionMatrix()

    def overlook(self, x: float, z: float, ground: float) -> None:
        """Place the editor's camera raised behind the point ``(x, z)`` at ``ground`` height, looking down the track."""
        self._eye = (x, ground + self.EDITOR_HEIGHT, z + self.EDITOR_DISTANCE)
        self._look = (x, ground, z - self.EDITOR_LOOK_AHEAD)
        self._camera_position = list(self._eye)
        self.camera.position.set(*self._eye)
        self.camera.lookAt(*self._look)
        self.camera.fov = self.BASE_FOV
        self.camera.updateProjectionMatrix()

    def reflect_on(self, ship: Ship, deck: float | None) -> None:
        """Mirror ``ship`` in the deck at height ``deck`` under it (None over a gap)."""
        self.reflection.place((ship.position.x, ship.position.y, -ship.position.z), deck)

    def render(self) -> None:
        """Render a frame: the ship's mirror image first, then the scene through post-processing."""
        self.reflection.render(self.renderer, self.scene, self.camera, self._eye, self._look)
        self.composer.render()  # each pass binds its own target, the mirror's included
