# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The ship's 3D model."""

from __future__ import annotations

import math
from itertools import pairwise
from typing import TYPE_CHECKING

from synthride.core.game_phase import GamePhase
from synthride.web.palette import Palette

if TYPE_CHECKING:
    from collections.abc import Sequence

    from synthride.core.ship import Ship
    from synthride.web.js_bridge import JsBridge, JsObject
    from synthride.web.neon_lines import NeonLines

Point = tuple[float, float, float]
Ring = tuple[Point, ...]


def _section(z: float, half_width: float, bottom: float, top: float) -> Ring:
    """Return a chamfered hexagonal cross-section of the body at depth ``z``."""
    w, shoulder = half_width, bottom + 0.55 * (top - bottom)
    return tuple(
        (x, y, z)
        for x, y in (
            (-0.85 * w, bottom),
            (0.85 * w, bottom),
            (w, shoulder),
            (0.75 * w, top),
            (-0.75 * w, top),
            (-w, shoulder),
        )
    )


def _slab(  # noqa: PLR0913
    z: float, half_bottom: float, half_top: float, bottom: float, top: float, *, x: float = 0.0
) -> Ring:
    """Return a trapezoid cross-section centred on ``x`` at depth ``z``."""
    return ((x - half_bottom, bottom, z), (x + half_bottom, bottom, z), (x + half_top, top, z), (x - half_top, top, z))


def _circle(x: float, y: float, radius: float, z: float, sides: int) -> Ring:
    """Return a regular polygon of ``sides`` around (``x``, ``y``) at depth ``z``, standing in for a circle."""
    return tuple(
        (x + radius * math.cos(2 * math.pi * i / sides), y + radius * math.sin(2 * math.pi * i / sides), z)
        for i in range(sides)
    )


def _fan(ring: Ring) -> list[Point]:
    """Triangles filling a convex ring from its centre."""
    center = tuple(sum(axis) / len(ring) for axis in zip(*ring, strict=True))
    triangles: list[Point] = []
    for i in range(len(ring)):
        triangles += (center, ring[i], ring[(i + 1) % len(ring)])
    return triangles


def _runner(x: float, half_width: float) -> tuple[Ring, ...]:
    """Return a runner centred on ``x``: curled up at its tip, then lying flat on the ground under the body."""
    return (
        _slab(-0.36, half_width, half_width, 0.05, 0.075, x=x),
        _slab(-0.3, half_width, half_width, 0.0, 0.04, x=x),
        _slab(0.34, half_width, half_width, 0.0, 0.04, x=x),
    )


class ShipModel:
    """The low-poly wedge sled, its glowing reactor, contact shadow and explosion, kept in sync with the simulated ship.

    An 80s supercar wedge riding two runners on the deck. Banking lifts the body just enough that the low
    runner stays on the surface instead of sinking into it.
    """

    # Cross-sections from the blade nose (-z) to the tail: the top rises in one long slope, outrun style.
    BODY = (
        _section(-0.4, 0.07, 0.05, 0.065),
        _section(-0.26, 0.23, 0.04, 0.11),
        _section(-0.05, 0.33, 0.04, 0.165),
        _section(0.3, 0.33, 0.04, 0.195),
        _section(0.38, 0.31, 0.05, 0.19),
    )
    CANOPY = (
        _slab(-0.16, 0.17, 0.15, 0.14, 0.145),
        _slab(-0.02, 0.18, 0.11, 0.165, 0.26),
        _slab(0.14, 0.18, 0.11, 0.18, 0.255),
        _slab(0.26, 0.17, 0.15, 0.19, 0.195),
    )
    RUNNER_X = 0.24
    RUNNER_HALF_WIDTH = 0.025
    RUNNERS = (_runner(-RUNNER_X, RUNNER_HALF_WIDTH), _runner(RUNNER_X, RUNNER_HALF_WIDTH))
    SPOILER = tuple(((x, 0.255, 0.28), (x, 0.255, 0.38), (x, 0.275, 0.38), (x, 0.285, 0.29)) for x in (-0.31, 0.31))
    STRUTS = tuple(
        tuple(
            ((x - 0.015, y, 0.31), (x + 0.015, y, 0.31), (x + 0.015, y, 0.36), (x - 0.015, y, 0.36))
            for y in (0.18, 0.26)
        )
        for x in (-0.2, 0.2)
    )
    # Twin round thrusters sit in the tail, each pushing out a slim flame: nested cones, hot white inside and
    # glow-coloured outside, fading to nothing at their tips and stretching with speed. A thin light bar runs
    # across the tail above them.
    NOZZLE_X = (-0.17, 0.17)
    NOZZLE_Y = 0.115
    NOZZLE_RADIUS = 0.048
    NOZZLE_DEPTH = (0.33, 0.395)  # front and back of the housing, the back just behind the tail
    NOZZLE_SIDES = 10
    FLAME_LAYERS = ((1.3, 0.75, 0.35), (0.95, 0.45, 0.7), (0.55, 0.2, 1.0))  # radius factor, length, brightness
    FLAME_STATIONS = 6  # rings along each cone; brightness falls off towards the tip
    FLAME_CORE_WHITENESS = 0.6  # how much the innermost cone is mixed towards white
    FLAME_FLICKER = 0.12
    TAIL_BAR = (0.27, 0.152, 0.165)  # half width, bottom, top
    REACTOR_LIGHTS_X = NOZZLE_X  # one light per thruster to wash the deck behind
    REACTOR_LIGHT_INTENSITY = 0.45
    BANK_PER_SPEED = 0.07  # in the air
    GROUND_BANK_PER_SPEED = 0.025  # a grounded sled only leans on its runners
    CONTACT_HALF_WIDTH = RUNNER_X + RUNNER_HALF_WIDTH
    CONTACT_HALF_LENGTH = 0.34
    FOOTPRINT = (0.33, 0.4)  # half width and half length of the body seen from above
    SHADOW_LIFT = 0.002
    GROUND_TILT_RATE = 14.0  # how fast the model settles onto a new slope
    SHADOW_LAYERS = (1.2, 1.05, 0.92)  # nested ellipses, relative to the footprint: darkest under the hull
    SHADOW_OPACITY = 0.28
    LINE_WIDTH = 3.0
    EXPLOSION_GROWTH = 5.0

    def __init__(self, bridge: JsBridge, lines: NeonLines) -> None:
        """Build the ship's meshes, reactor, shadow and explosion."""
        self._bridge = bridge
        self._lines = lines
        three = bridge.three
        self.group = three.Group.new()
        self.body = three.Group.new()
        self.group.add(self.body)
        hull_material = three.MeshStandardMaterial.new(
            bridge.obj(
                color=Palette.SHIP_BODY,
                emissive=Palette.SHIP_GLOW,
                emissiveIntensity=0.15,
                metalness=0.8,
                roughness=0.25,
                flatShading=True,
                side=three.DoubleSide,
            )
        )
        canopy_material = three.MeshStandardMaterial.new(
            bridge.obj(
                color=Palette.SHIP_BODY,
                emissive=Palette.SHIP_EDGE,
                emissiveIntensity=0.35,
                metalness=0.9,
                roughness=0.1,
                flatShading=True,
                side=three.DoubleSide,
            )
        )
        self._add_solid(self._lofted(self.BODY), hull_material, self.body)
        self._add_solid(self._lofted(self.CANOPY), canopy_material, self.body)
        for part in (*self.RUNNERS, self.SPOILER, *self.STRUTS):
            self._add_solid(self._lofted(part), hull_material, self.body)
        self.plume = self._reactor(hull_material)
        self.shadow = self._contact_shadow()
        self.group.add(self.shadow)
        self._explosion_material = three.MeshBasicMaterial.new(
            bridge.obj(color=Palette.EXPLOSION, wireframe=True, transparent=True, opacity=1.0)
        )
        self.explosion = three.Mesh.new(three.IcosahedronGeometry.new(0.4, 1), self._explosion_material)
        self.explosion.visible = False
        self.group.add(self.explosion)
        self._explosion_age = 0.0
        self._time = 0.0
        self._ground_tilt: tuple[float, ...] = (0.0, 0.0)  # eased (roll, pitch) of the ground under the ship

    @staticmethod
    def _lofted(rings: Sequence[Ring]) -> list[Point]:
        """Triangles skinning consecutive rings of matching size, with both end rings capped by a fan."""
        triangles: list[Point] = []
        for lower, upper in pairwise(rings):
            for i in range(len(lower)):
                j = (i + 1) % len(lower)
                triangles += (lower[i], lower[j], upper[j], lower[i], upper[j], upper[i])
        return triangles + _fan(rings[0]) + _fan(rings[-1])

    def _glow_material(self, color: int, opacity: float = 1.0, *, vertex_colors: bool = False) -> JsObject:
        three = self._bridge.three
        return three.MeshBasicMaterial.new(
            self._bridge.obj(
                color=color,
                vertexColors=vertex_colors,
                transparent=True,
                opacity=opacity,
                blending=three.AdditiveBlending,
                depthWrite=False,
                side=three.DoubleSide,
            )
        )

    def _glow_mesh(self, triangles: list[Point], material: JsObject) -> JsObject:
        three = self._bridge.three
        geometry = three.BufferGeometry.new()
        geometry.setAttribute(
            "position", three.BufferAttribute.new(self._bridge.float32_array([c for v in triangles for c in v]), 3)
        )
        return three.Mesh.new(geometry, material)

    def _reactor(self, housing_material: JsObject) -> JsObject:
        """Fit the thrusters, their glowing throats and flames, the tail light bar and the deck lights.

        Returns the plume group holding the flames, which ``sync`` stretches backwards with speed.
        """
        three = self._bridge.three
        front, back = self.NOZZLE_DEPTH
        bar_half, bar_bottom, bar_top = self.TAIL_BAR
        bar = _slab(back + 0.001, bar_half, bar_half, bar_bottom, bar_top)
        self.body.add(self._glow_mesh(_fan(bar), self._glow_material(Palette.SHIP_GLOW, 0.9)))
        throat_material = self._glow_material(Palette.mix(Palette.SHIP_GLOW, 0xFFFFFF, 0.45))
        plume = three.Group.new()
        plume.position.z = back
        for x in self.NOZZLE_X:
            housing = (
                _circle(x, self.NOZZLE_Y, self.NOZZLE_RADIUS * 1.1, front, self.NOZZLE_SIDES),
                _circle(x, self.NOZZLE_Y, self.NOZZLE_RADIUS * 1.25, back, self.NOZZLE_SIDES),
            )
            self._add_solid(self._lofted(housing), housing_material, self.body)
            throat = _circle(x, self.NOZZLE_Y, self.NOZZLE_RADIUS, back + 0.002, self.NOZZLE_SIDES)
            self.body.add(self._glow_mesh(_fan(throat), throat_material))
            for i, (factor, length, brightness) in enumerate(self.FLAME_LAYERS):
                whiteness = self.FLAME_CORE_WHITENESS * i / (len(self.FLAME_LAYERS) - 1)
                color = Palette.mix(Palette.SHIP_GLOW, 0xFFFFFF, whiteness)
                plume.add(self._flame(x, self.NOZZLE_RADIUS * factor, length, color, brightness))
        self.body.add(plume)
        for x in self.REACTOR_LIGHTS_X:
            light = three.PointLight.new(Palette.SHIP_GLOW, self.REACTOR_LIGHT_INTENSITY, 2.5)
            light.position.set(x, self.NOZZLE_Y, back + 0.15)
            self.body.add(light)
        return plume

    def _flame(self, x: float, radius: float, length: float, color: int, brightness: float) -> JsObject:
        """Return a cone streaming back from the nozzle at ``x``, fading to black (so to nothing, added) at its tip."""
        three = self._bridge.three
        stations = [i / self.FLAME_STATIONS for i in range(self.FLAME_STATIONS + 1)]
        rings = [_circle(x, self.NOZZLE_Y, radius * (1 - t) ** 0.7, length * t, self.NOZZLE_SIDES) for t in stations]
        fades = [brightness * (1 - t) ** 2 for t in stations]
        triangles: list[Point] = []
        shades: list[float] = []
        for (lower, upper), (near, far) in zip(pairwise(rings), pairwise(fades), strict=True):
            for i in range(self.NOZZLE_SIDES):
                j = (i + 1) % self.NOZZLE_SIDES
                triangles += (lower[i], lower[j], upper[j], lower[i], upper[j], upper[i])
                shades += (near, near, far, near, far, far)
        rgb = [((color >> shift) & 0xFF) / 255 for shift in (16, 8, 0)]
        mesh = self._glow_mesh(triangles, self._glow_material(0xFFFFFF, vertex_colors=True))
        mesh.geometry.setAttribute(
            "color",
            three.BufferAttribute.new(self._bridge.float32_array([c * shade for shade in shades for c in rgb]), 3),
        )
        return mesh

    def _contact_shadow(self) -> JsObject:
        """Soft darkening of the deck under the hull: stacked translucent ellipses, darkest at the centre."""
        three = self._bridge.three
        material = three.MeshBasicMaterial.new(
            self._bridge.obj(
                color=0x000000,
                transparent=True,
                opacity=self.SHADOW_OPACITY,
                depthWrite=False,
                polygonOffset=True,
                polygonOffsetFactor=-2,
            )
        )
        shadow = three.Group.new()
        shadow.position.y = self.SHADOW_LIFT
        for scale in self.SHADOW_LAYERS:
            layer = three.Mesh.new(three.CircleGeometry.new(1, 24), material)
            layer.rotation.x = -math.pi / 2
            layer.scale.set(self.FOOTPRINT[0] * scale, self.FOOTPRINT[1] * scale, 1)
            shadow.add(layer)
        return shadow

    def _add_solid(self, triangles: list[Point], material: JsObject, parent: JsObject) -> None:
        three = self._bridge.three
        geometry = three.BufferGeometry.new()
        geometry.setAttribute(
            "position", three.BufferAttribute.new(self._bridge.float32_array([c for v in triangles for c in v]), 3)
        )
        geometry.computeVertexNormals()
        self._add_outlined(geometry, material, parent)

    def _add_outlined(self, geometry: JsObject, material: JsObject, parent: JsObject) -> None:
        parent.add(self._bridge.three.Mesh.new(geometry, material))
        parent.add(self._lines.edges_of(geometry, Palette.SHIP_EDGE, self.LINE_WIDTH))

    def sync(self, ship: Ship, phase: GamePhase, dt: float) -> None:
        """Place, tilt and animate the model to match ``ship``."""
        self._time += dt
        position = ship.position
        self.group.position.set(position.x, position.y, -position.z)
        exploding = phase is GamePhase.DYING
        self.body.visible = not exploding
        self.shadow.visible = not exploding and ship.grounded
        self.explosion.visible = exploding
        if exploding:
            self._explode(dt)
            return
        self._explosion_age = 0.0
        bank = -ship.velocity.x * (self.GROUND_BANK_PER_SPEED if ship.grounded else self.BANK_PER_SPEED)
        pitch = max(-0.3, min(0.3, ship.velocity.y * 0.04))
        # On a slope the model eases into lying along the ground. The ship rests on the highest point under it,
        # which on a slope is above the ground under its centre, so the body comes down to meet it.
        blend = 1 - math.exp(-self.GROUND_TILT_RATE * dt)
        self._ground_tilt = tuple(
            angle + (math.atan(slope) - angle) * blend
            for angle, slope in zip(self._ground_tilt, ship.ground_slope, strict=True)
        )
        roll, rise = self._ground_tilt
        self.body.rotation.z = bank + roll
        self.body.rotation.x = pitch + rise
        sink = abs(math.tan(roll)) * ship.width / 2 + abs(math.tan(rise)) * ship.length / 2
        self.shadow.rotation.z = roll
        self.shadow.rotation.x = rise
        self.shadow.position.y = self.SHADOW_LIFT - sink
        # Lift by what the tilt would push the low runner below the ground, so it stays in contact.
        self.body.position.y = (
            self.CONTACT_HALF_WIDTH * abs(math.sin(bank)) + self.CONTACT_HALF_LENGTH * abs(math.sin(pitch)) - sink
        )
        flicker = self.FLAME_FLICKER * (math.sin(self._time * 47) + 0.5 * math.sin(self._time * 83))
        self.plume.scale.z = 0.5 + 1.5 * min(ship.speed, 40) / 40 + flicker

    def _explode(self, dt: float) -> None:
        self._explosion_age += dt
        self.explosion.scale.setScalar(1 + self._explosion_age * self.EXPLOSION_GROWTH)
        self.explosion.rotation.y = self._explosion_age * 3
        self._explosion_material.opacity = max(0.0, 1 - self._explosion_age)
