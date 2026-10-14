from __future__ import annotations

import math
from collections.abc import Sequence
from itertools import pairwise
from typing import Any

from synthride.core.game_phase import GamePhase
from synthride.core.ship import Ship
from synthride.web.js_bridge import JsBridge
from synthride.web.neon_lines import NeonLines
from synthride.web.palette import Palette

Point = tuple[float, float, float]
Ring = tuple[Point, ...]


def _section(z: float, half_width: float, bottom: float, top: float) -> Ring:
    """A chamfered hexagonal cross-section of the body at depth ``z``."""
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


def _slab(z: float, half_bottom: float, half_top: float, bottom: float, top: float, x: float = 0.0) -> Ring:
    """A trapezoid cross-section centred on ``x`` at depth ``z``."""
    return ((x - half_bottom, bottom, z), (x + half_bottom, bottom, z), (x + half_top, top, z), (x - half_top, top, z))


def _scaled(ring: Ring, factor: float, z: float) -> Ring:
    """``ring`` shrunk or grown by ``factor`` about its centre, moved to depth ``z``."""
    cx, cy = (sum(axis) / len(ring) for axis in tuple(zip(*ring, strict=True))[:2])
    return tuple((cx + (x - cx) * factor, cy + (y - cy) * factor, z) for x, y, _ in ring)


def _fan(ring: Ring) -> list[Point]:
    """Triangles filling a convex ring from its centre."""
    center = tuple(sum(axis) / len(ring) for axis in zip(*ring, strict=True))
    triangles: list[Point] = []
    for i in range(len(ring)):
        triangles += (center, ring[i], ring[(i + 1) % len(ring)])
    return triangles


def _runner(x: float, half_width: float) -> tuple[Ring, ...]:
    """A runner centred on ``x``: curled up at its tip, then lying flat on the ground under the body."""
    return (
        _slab(-0.36, half_width, half_width, 0.05, 0.075, x),
        _slab(-0.3, half_width, half_width, 0.0, 0.04, x),
        _slab(0.34, half_width, half_width, 0.0, 0.04, x),
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
    # The whole tail is the reactor nozzle: its face glows edge to edge, a hot core sits in the middle, and
    # nested translucent shells trail behind as the plume, stretching with speed.
    REACTOR_Z = 0.384  # just behind the tail
    REACTOR_FACE = 0.88  # of the tail section, leaving the outline visible
    REACTOR_CORE = 0.5
    PLUME_LAYERS = ((0.95, 0.12, 0.22), (0.8, 0.25, 0.12), (0.6, 0.4, 0.06))  # exit size, length, opacity
    PLUME_TIP = 0.6  # of the exit size, at the far end of each shell
    REACTOR_LIGHTS_X = (-0.22, 0.0, 0.22)  # a row of lights so the deck glows across the whole width
    REACTOR_LIGHT_INTENSITY = 0.6
    BANK_PER_SPEED = 0.07  # in the air
    GROUND_BANK_PER_SPEED = 0.025  # a grounded sled only leans on its runners
    CONTACT_HALF_WIDTH = RUNNER_X + RUNNER_HALF_WIDTH
    CONTACT_HALF_LENGTH = 0.34
    FOOTPRINT = (0.33, 0.4)  # half width and half length of the body seen from above
    SHADOW_LAYERS = (1.2, 1.05, 0.92)  # nested ellipses, relative to the footprint: darkest under the hull
    SHADOW_OPACITY = 0.28
    LINE_WIDTH = 3.0
    EXPLOSION_GROWTH = 5.0

    def __init__(self, bridge: JsBridge, lines: NeonLines) -> None:
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
        self.plume = self._reactor()
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

    @staticmethod
    def _lofted(rings: Sequence[Ring]) -> list[Point]:
        """Triangles skinning consecutive rings of matching size, with both end rings capped by a fan."""
        triangles: list[Point] = []
        for lower, upper in pairwise(rings):
            for i in range(len(lower)):
                j = (i + 1) % len(lower)
                triangles += (lower[i], lower[j], upper[j], lower[i], upper[j], upper[i])
        return triangles + _fan(rings[0]) + _fan(rings[-1])

    def _glow_material(self, color: int, opacity: float = 1.0) -> Any:
        three = self._bridge.three
        return three.MeshBasicMaterial.new(
            self._bridge.obj(
                color=color,
                transparent=True,
                opacity=opacity,
                blending=three.AdditiveBlending,
                depthWrite=False,
                side=three.DoubleSide,
            )
        )

    def _glow_mesh(self, triangles: list[Point], material: Any) -> Any:
        three = self._bridge.three
        geometry = three.BufferGeometry.new()
        geometry.setAttribute(
            "position", three.BufferAttribute.new(self._bridge.float32_array([c for v in triangles for c in v]), 3)
        )
        return three.Mesh.new(geometry, material)

    def _reactor(self) -> Any:
        """Light the whole tail: a glowing nozzle face, a hot core, a plume of shells and a row of lights.

        Returns the plume group, which ``sync`` stretches backwards with speed.
        """
        three = self._bridge.three
        tail = self.BODY[-1]
        face = _scaled(tail, self.REACTOR_FACE, self.REACTOR_Z)
        core = _scaled(tail, self.REACTOR_CORE, self.REACTOR_Z + 0.001)
        self.body.add(self._glow_mesh(_fan(face), self._glow_material(Palette.SHIP_GLOW)))
        self.body.add(self._glow_mesh(_fan(core), self._glow_material(Palette.mix(Palette.SHIP_GLOW, 0xFFFFFF, 0.6))))
        plume = three.Group.new()
        plume.position.z = self.REACTOR_Z
        for size, length, opacity in self.PLUME_LAYERS:
            exit_ring = _scaled(tail, size, 0.0)
            shell = (exit_ring, _scaled(exit_ring, self.PLUME_TIP, length))
            plume.add(self._glow_mesh(self._lofted(shell), self._glow_material(Palette.SHIP_GLOW, opacity)))
        self.body.add(plume)
        _, centre_y, _ = (sum(axis) / len(tail) for axis in zip(*tail, strict=True))
        for x in self.REACTOR_LIGHTS_X:
            light = three.PointLight.new(Palette.SHIP_GLOW, self.REACTOR_LIGHT_INTENSITY, 2.5)
            light.position.set(x, centre_y, self.REACTOR_Z + 0.15)
            self.body.add(light)
        return plume

    def _contact_shadow(self) -> Any:
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
        shadow.position.y = 0.002
        for scale in self.SHADOW_LAYERS:
            layer = three.Mesh.new(three.CircleGeometry.new(1, 24), material)
            layer.rotation.x = -math.pi / 2
            layer.scale.set(self.FOOTPRINT[0] * scale, self.FOOTPRINT[1] * scale, 1)
            shadow.add(layer)
        return shadow

    def _add_solid(self, triangles: list[Point], material: Any, parent: Any) -> None:
        three = self._bridge.three
        geometry = three.BufferGeometry.new()
        geometry.setAttribute(
            "position", three.BufferAttribute.new(self._bridge.float32_array([c for v in triangles for c in v]), 3)
        )
        geometry.computeVertexNormals()
        self._add_outlined(geometry, material, parent)

    def _add_outlined(self, geometry: Any, material: Any, parent: Any) -> None:
        parent.add(self._bridge.three.Mesh.new(geometry, material))
        parent.add(self._lines.edges_of(geometry, Palette.SHIP_EDGE, self.LINE_WIDTH))

    def sync(self, ship: Ship, phase: GamePhase, dt: float) -> None:
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
        self.body.rotation.z = bank
        self.body.rotation.x = pitch
        # Lift by what the tilt would push the low runner below the ground, so it stays in contact.
        self.body.position.y = self.CONTACT_HALF_WIDTH * abs(math.sin(bank)) + self.CONTACT_HALF_LENGTH * abs(
            math.sin(pitch)
        )
        self.plume.scale.z = 1 + min(ship.speed, 20) / 20 + 0.15 * math.sin(self._time * 40)

    def _explode(self, dt: float) -> None:
        self._explosion_age += dt
        self.explosion.scale.setScalar(1 + self._explosion_age * self.EXPLOSION_GROWTH)
        self.explosion.rotation.y = self._explosion_age * 3
        self._explosion_material.opacity = max(0.0, 1 - self._explosion_age)
