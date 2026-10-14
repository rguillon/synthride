# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""A glossy mirror image of the ship on the deck below it."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synthride.web.js_bridge import JsBridge, JsObject

Point = tuple[float, float, float]


class ShipReflection:
    """Mirrors the ship in the deck it flies over, as a planar reflection.

    Each frame a virtual camera, the main camera mirrored through the deck plane, renders only the
    objects on ``LAYER`` (the ship) into a half-resolution target. Patched tile materials project their
    top faces through that camera to sample the target, and add what they find to their light, fading
    with distance from the ship and away from the deck's height (other decks would mirror it misplaced).
    """

    LAYER = 1
    STRENGTH = 0.3
    INNER_REACH = 1.2  # full reflection within this distance of the ship, along the deck
    OUTER_REACH = 3.0
    FADE_START = 0.6  # height above the deck where the reflection starts dimming, gone by FADE_END
    FADE_END = 4.0
    RESOLUTION = 0.5  # of the screen: cheaper, and softens the mirror into a gloss

    VERTEX_HEADER = "varying vec3 vReflectWorld;\nvarying float vReflectUp;\n"
    VERTEX_BODY = """#include <project_vertex>
vReflectWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;
vReflectUp = normalize(mat3(modelMatrix) * objectNormal).y;"""
    FRAGMENT_HEADER = """uniform sampler2D reflectionMap;
uniform mat4 reflectionMatrix;
uniform vec3 reflectionCentre;
uniform float reflectionStrength;
uniform vec2 reflectionReach;
varying vec3 vReflectWorld;
varying float vReflectUp;
"""
    FRAGMENT_BODY = """if (reflectionStrength > 0.0) {
  vec4 reflectCoord = reflectionMatrix * vec4(vReflectWorld, 1.0);
  if (reflectCoord.w > 0.0) {
    vec2 reflectUv = reflectCoord.xy / reflectCoord.w;
    vec2 tap = vec2(0.0025, 0.004);
    vec3 reflected = 0.4 * texture2D(reflectionMap, reflectUv).rgb
      + 0.15 * texture2D(reflectionMap, reflectUv + vec2(tap.x, 0.0)).rgb
      + 0.15 * texture2D(reflectionMap, reflectUv - vec2(tap.x, 0.0)).rgb
      + 0.15 * texture2D(reflectionMap, reflectUv + vec2(0.0, tap.y)).rgb
      + 0.15 * texture2D(reflectionMap, reflectUv - vec2(0.0, tap.y)).rgb;
    float reach = 1.0 - smoothstep(reflectionReach.x, reflectionReach.y,
      distance(vReflectWorld.xz, reflectionCentre.xz));
    float facing = smoothstep(0.7, 0.95, vReflectUp);
    float level = 1.0 - smoothstep(0.1, 0.4, abs(vReflectWorld.y - reflectionCentre.y));
    outgoingLight += reflected * reflectionStrength * reach * facing * level;
  }
}
#include <opaque_fragment>"""

    def __init__(self, bridge: JsBridge) -> None:
        """Create the mirror camera, its render target and the uniforms patched materials share."""
        three = bridge.three
        self._bridge = bridge
        self.target = three.WebGLRenderTarget.new(1, 1, bridge.obj(type=three.HalfFloatType))
        self.camera = three.PerspectiveCamera.new(50, 1, 0.1, 1500)
        self.camera.layers.set(self.LAYER)
        self._matrix = three.Matrix4.new()
        self._centre = three.Vector3.new()
        self._strength = three.Uniform.new(0.0)
        self._uniforms = {
            "reflectionMap": three.Uniform.new(self.target.texture),
            "reflectionMatrix": three.Uniform.new(self._matrix),
            "reflectionCentre": three.Uniform.new(self._centre),
            "reflectionStrength": self._strength,
            "reflectionReach": three.Uniform.new(three.Vector2.new(self.INNER_REACH, self.OUTER_REACH)),
        }
        self._patch_proxy = bridge.proxy(self._patch)
        self._deck: float | None = None
        self.strength = 0.0

    def resize(self, width: int, height: int) -> None:
        """Fit the mirror image to a ``width`` x ``height`` screen."""
        self.target.setSize(max(int(width * self.RESOLUTION), 1), max(int(height * self.RESOLUTION), 1))

    def include(self, item: JsObject) -> None:
        """Show ``item`` and everything under it in the mirror."""
        item.traverse(self._bridge.proxy(lambda child: child.layers.enable(self.LAYER)))

    def patch(self, material: JsObject) -> None:
        """Make the top faces drawn with ``material`` show the reflection."""
        material.onBeforeCompile = self._patch_proxy

    def place(self, ship: Point, deck: float | None) -> None:
        """Mirror the ship at world position ``ship`` in the deck at height ``deck`` (None over a gap)."""
        self._deck = deck
        if deck is None:
            self.strength = 0.0
            return
        x, y, z = ship
        self._centre.set(x, deck, z)
        lift = (y - deck - self.FADE_START) / (self.FADE_END - self.FADE_START)
        self.strength = self.STRENGTH * min(max(1.0 - lift, 0.0), 1.0)

    def render(self, renderer: JsObject, scene: JsObject, camera: JsObject, eye: Point, look: Point) -> None:
        """Render the mirror image seen by ``camera``, placed at ``eye`` and looking at ``look``.

        This leaves the mirror target bound: whatever renders next must pick its own target.
        """
        self._strength.value = self.strength
        if self.strength <= 0.0 or self._deck is None:
            return
        deck, mirror = self._deck, self.camera
        mirror.position.set(eye[0], 2 * deck - eye[1], eye[2])
        mirror.up.set(0, -1, 0)  # the main camera's up, mirrored
        mirror.lookAt(look[0], 2 * deck - look[1], look[2])
        mirror.fov, mirror.aspect = camera.fov, camera.aspect
        mirror.updateProjectionMatrix()
        mirror.updateMatrixWorld()
        # Maps a world position to its spot in the mirror image, from clip space to texture space.
        self._matrix.set(0.5, 0, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0, 0.5, 0.5, 0, 0, 0, 1)
        self._matrix.multiply(mirror.projectionMatrix)
        self._matrix.multiply(mirror.matrixWorldInverse)
        renderer.setRenderTarget(self.target)
        renderer.render(scene, mirror)

    def _patch(self, shader: JsObject, *_: object) -> None:
        for name, uniform in self._uniforms.items():
            setattr(shader.uniforms, name, uniform)
        shader.vertexShader = self.VERTEX_HEADER + shader.vertexShader.replace(
            "#include <project_vertex>", self.VERTEX_BODY
        )
        shader.fragmentShader = self.FRAGMENT_HEADER + shader.fragmentShader.replace(
            "#include <opaque_fragment>", self.FRAGMENT_BODY
        )
