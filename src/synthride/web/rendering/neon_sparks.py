# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Neon sparks thrown off by impacts."""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from synthride.core.gameplay.game_event import GameEvent
from synthride.web.rendering.palette import Palette

if TYPE_CHECKING:
    from collections.abc import Sequence

    from synthride.core.gameplay.ship import Ship
    from synthride.web.browser.js_bridge import JsBridge, JsObject

Point = tuple[float, float, float]


@dataclass(frozen=True)
class SparkBurst:
    """How a burst of sparks looks and flies."""

    count: int
    speed: tuple[float, float]
    life: tuple[float, float]
    size: tuple[float, float]
    colors: Sequence[int]
    inherit: float  # of the ship's velocity the sparks keep
    glow: float  # HDR brightness, so the bloom catches them


class NeonSparks:
    """Glowing sparks: a shower where the ship scrapes a wall and a big burst when it is destroyed.

    Each spark's start, velocity and birth time are written once into a ring buffer; the vertex shader flies
    it from there under drag and gravity and fades it out, so living sparks cost nothing in Python.
    """

    CAPACITY = 2048
    DEATHS = frozenset({
        GameEvent.CRASHED,
        GameEvent.BURNED,
        GameEvent.FELL,
        GameEvent.OUT_OF_FUEL,
        GameEvent.OUT_OF_OXYGEN,
    })
    GRAVITY = 12.0
    DRAG = 2.5
    SCRAPE = SparkBurst(
        count=4, speed=(1.5, 4.5), life=(0.25, 0.55), size=(0.6, 1.2), colors=Palette.SPARKS, inherit=0.55, glow=3.0
    )
    IMPACT = SparkBurst(
        count=28, speed=(2.0, 6.0), life=(0.3, 0.7), size=(0.7, 1.4), colors=Palette.SPARKS, inherit=0.4, glow=3.0
    )
    DEATH = SparkBurst(
        count=420,
        speed=(3.0, 15.0),
        life=(0.7, 1.9),
        size=(1.0, 2.6),
        colors=(*Palette.SPARKS, Palette.EXPLOSION, Palette.GRID),
        inherit=0.15,
        glow=4.0,
    )
    VERTEX = """
        attribute vec3 aVelocity;
        attribute vec3 aColor;
        attribute float aBirth;
        attribute float aLife;
        attribute float aSize;
        uniform float uTime;
        uniform float uGravity;
        uniform float uDrag;
        uniform float uPixelRatio;
        varying vec3 vColor;
        varying float vFade;
        void main() {
            float age = uTime - aBirth;
            if (age < 0.0 || age > aLife) {
                gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
                gl_PointSize = 0.0;
                return;
            }
            vec3 p = position + aVelocity * (1.0 - exp(-uDrag * age)) / uDrag;
            p.y -= 0.5 * uGravity * age * age;
            vFade = 1.0 - age / aLife;
            float flicker = 0.75 + 0.25 * sin(age * 70.0 + aBirth * 911.0);
            vColor = aColor * flicker;
            vec4 view = modelViewMatrix * vec4(p, 1.0);
            gl_PointSize = clamp(aSize * uPixelRatio * 30.0 / max(-view.z, 0.1) * (0.35 + 0.65 * vFade), 1.0, 48.0);
            gl_Position = projectionMatrix * view;
        }
    """
    FRAGMENT = """
        varying vec3 vColor;
        varying float vFade;
        void main() {
            float d = length(gl_PointCoord - 0.5);
            if (d > 0.5) discard;
            float halo = 1.0 - smoothstep(0.0, 0.5, d);
            float core = 1.0 - smoothstep(0.0, 0.18, d);
            gl_FragColor = vec4(mix(vColor * halo, vec3(halo * 2.0), core * vFade) * vFade, 1.0);
        }
    """

    def __init__(self, bridge: JsBridge, rng: random.Random | None = None) -> None:
        """Allocate the spark buffers, every spark dead."""
        self._bridge = bridge
        self._rng = rng or random.Random()  # noqa: S311
        self._time = 0.0
        self._next = 0
        three = bridge.three
        geometry = three.BufferGeometry.new()
        self._attributes: dict[str, tuple[JsObject, int]] = {}
        for name, size, fill in (
            ("position", 3, 0.0),
            ("aVelocity", 3, 0.0),
            ("aColor", 3, 0.0),
            ("aBirth", 1, -1e6),
            ("aLife", 1, 0.0),
            ("aSize", 1, 0.0),
        ):
            attribute = three.BufferAttribute.new(bridge.float32_array([fill] * self.CAPACITY * size), size)
            attribute.setUsage(three.DynamicDrawUsage)
            geometry.setAttribute(name, attribute)
            self._attributes[name] = attribute, size
        self.material = three.ShaderMaterial.new(
            bridge.obj(
                uniforms={
                    "uTime": {"value": 0.0},
                    "uGravity": {"value": self.GRAVITY},
                    "uDrag": {"value": self.DRAG},
                    "uPixelRatio": {"value": min(bridge.window.devicePixelRatio, 2)},
                },
                vertexShader=self.VERTEX,
                fragmentShader=self.FRAGMENT,
                blending=three.AdditiveBlending,
                transparent=True,
                depthWrite=False,
            )
        )
        self.points = three.Points.new(geometry, self.material)
        self.points.frustumCulled = False  # the shader flies every spark away from where the geometry says

    def react(self, events: list[GameEvent], ship: Ship) -> None:
        """Throw sparks off the walls the ship scraped or hit, and a big burst when it is destroyed."""
        counts = Counter(events)
        x, y, z = ship.position.x, ship.position.y, -ship.position.z
        velocity = (ship.velocity.x, ship.velocity.y, -ship.velocity.z)
        half_width, half_length = ship.width / 2, ship.length / 2
        for event, side in ((GameEvent.SCRAPED_LEFT, -1), (GameEvent.SCRAPED_RIGHT, 1)):
            for _ in range(counts[event]):
                # Off the wall, back toward the track, and up.
                self.emit((x + side * half_width, y + 0.08, z), self.SCRAPE, velocity, direction=(-side, 1.2, 0.4))
        if counts[GameEvent.NUDGED]:
            self.emit((x, y + 0.1, z - half_length), self.IMPACT, velocity, direction=(0.0, 1.0, 1.0))
        if counts[GameEvent.BUMPED]:
            self.emit((x, y + ship.height, z), self.IMPACT, velocity, direction=(0.0, -0.5, 0.0))
        if self.DEATHS & counts.keys():
            self.emit((x, y + ship.height / 2, z), self.DEATH, velocity)

    def emit(self, origin: Point, burst: SparkBurst, velocity: Point, direction: Point | None = None) -> None:
        """Throw ``burst`` from ``origin``, biased toward ``direction`` (every way when None)."""
        rng = self._rng
        count = min(burst.count, self.CAPACITY)
        if self._next + count > self.CAPACITY:
            self._next = 0
        values: dict[str, list[float]] = {name: [] for name in self._attributes}
        for _ in range(count):
            heading = self._random_direction()
            if direction is not None:
                heading = self._normalized(tuple(h + d for h, d in zip(heading, direction, strict=True)))
            speed = rng.uniform(*burst.speed)
            values["position"] += origin
            values["aVelocity"] += [h * speed + v * burst.inherit for h, v in zip(heading, velocity, strict=True)]
            values["aColor"] += [channel * burst.glow for channel in Palette.linear_rgb(rng.choice(burst.colors))]
            values["aBirth"].append(self._time)
            values["aLife"].append(rng.uniform(*burst.life))
            values["aSize"].append(rng.uniform(*burst.size))
        for name, (attribute, size) in self._attributes.items():
            attribute.array.set(self._bridge.float32_array(values[name]), self._next * size)
            attribute.needsUpdate = True
        self._next += count

    def update(self, dt: float) -> None:
        """Advance the sparks' clock."""
        self._time += dt
        self.material.uniforms.uTime.value = self._time

    def _random_direction(self) -> Point:
        """Return a uniformly random unit vector."""
        y = self._rng.uniform(-1.0, 1.0)
        angle = self._rng.uniform(0.0, 2 * math.pi)
        ring = math.sqrt(1 - y * y)
        return math.cos(angle) * ring, y, math.sin(angle) * ring

    @staticmethod
    def _normalized(vector: Sequence[float]) -> Point:
        length = math.sqrt(sum(c * c for c in vector)) or 1.0
        x, y, z = (c / length for c in vector)
        return x, y, z
