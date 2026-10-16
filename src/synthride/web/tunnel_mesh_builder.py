# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The tunnels' meshes."""

from __future__ import annotations

from itertools import pairwise
from typing import TYPE_CHECKING

from synthride.core.tunnel_kind import TunnelKind
from synthride.web.box_geometry_buffer import BoxGeometryBuffer, Rgb
from synthride.web.palette import Palette

if TYPE_CHECKING:
    from synthride.core.track import Track
    from synthride.core.tunnel_span import Point, TunnelSpan
    from synthride.web.js_bridge import JsBridge, JsObject
    from synthride.web.neon_lines import NeonLines


class TunnelMeshBuilder:
    """Turns a track's tunnels into shaded shells outlined in neon.

    Each span's cross-section is extruded along its row. Neon traces both outlines of every mouth, runs
    along the roof's ridges, and rings the inside at every row, so speed shows while riding through.
    """

    BODY_GLOW = 0.04
    MOUTH_WIDTH = 2.5
    RIB_WIDTH = 1.4
    RIB_COLOR = Palette.mix(Palette.TUNNEL, Palette.TILE_BODY, 0.35)
    LINE_LIFT = 0.004  # keeps mouth outlines off the end caps
    OUTER = Palette.linear_rgb(Palette.mix(Palette.TILE_BODY, Palette.TUNNEL, 0.22))
    INNER = Palette.linear_rgb(Palette.mix(Palette.TILE_BODY, Palette.TUNNEL, 0.07))
    CAP = Palette.linear_rgb(Palette.mix(Palette.TILE_BODY, Palette.TUNNEL, 0.3))

    def __init__(self, bridge: JsBridge, lines: NeonLines) -> None:
        """Create meshes with the bridge's Three.js and outline them with ``lines``."""
        self._bridge = bridge
        self._lines = lines
        self.material: JsObject = None

    def build(self, track: Track) -> list[JsObject]:
        """Return the shell mesh and its neon line sets, or nothing when the track has no tunnel."""
        if not track.tunnels:
            return []
        rows: dict[int, list[TunnelSpan]] = {}
        for span in track.tunnels:
            rows.setdefault(span.row, []).append(span)
        buffer = BoxGeometryBuffer()
        mouths: list[float] = []
        ribs: list[float] = []
        for span in track.tunnels:
            outer, inner = span.outer_path(), span.inner_path()
            self._add_shell(buffer, span, outer, inner)
            near, far = -span.start, -span.end
            self._trace(ribs, inner, (near + far) / 2)  # one rib per square, like the deck's seams
            if not any(span.continues(other) for other in rows.get(span.row - 1, ())):
                self._trace(mouths, outer, near + self.LINE_LIFT)
                self._trace(mouths, inner, near + self.LINE_LIFT)
            if any(span.continues(other) for other in rows.get(span.row + 1, ())):
                self._trace(ribs, inner, far)
            else:
                self._trace(mouths, outer, far - self.LINE_LIFT)
                self._trace(mouths, inner, far - self.LINE_LIFT)
            for x, y in self._ridges(span, outer):
                mouths += (x, y, near, x, y, far)
        three = self._bridge.three
        self.material = three.MeshStandardMaterial.new(
            self._bridge.obj(
                vertexColors=True,
                emissive=Palette.TUNNEL,
                emissiveIntensity=self.BODY_GLOW,
                roughness=0.5,
                metalness=0.3,
                polygonOffset=True,  # keeps the neon on top at a distance, like the track slabs
                polygonOffsetFactor=1,
                polygonOffsetUnits=4,
            )
        )
        geometry = three.BufferGeometry.new()
        for name, values in (("position", buffer.positions), ("normal", buffer.normals), ("color", buffer.colors)):
            geometry.setAttribute(name, three.BufferAttribute.new(self._bridge.float32_array(values), 3))
        return [
            three.Mesh.new(geometry, self.material),
            self._lines.segments(mouths, Palette.TUNNEL, self.MOUTH_WIDTH),
            self._lines.segments(ribs, self.RIB_COLOR, self.RIB_WIDTH),
        ]

    def _add_shell(self, buffer: BoxGeometryBuffer, span: TunnelSpan, outer: list[Point], inner: list[Point]) -> None:
        """Outer skin, inner skin and both end caps, as quads between consecutive points of the span's paths."""
        near, far = -span.start, -span.end
        for (p, q), (pi, qi) in zip(pairwise(outer), pairwise(inner), strict=True):
            self._quad(buffer, ((*p, near), (*q, near), (*q, far), (*p, far)), self.OUTER)
            self._quad(buffer, ((*qi, near), (*pi, near), (*pi, far), (*qi, far)), self.INNER)
            self._quad(buffer, ((*pi, near), (*qi, near), (*q, near), (*p, near)), self.CAP)
            self._quad(buffer, ((*p, far), (*q, far), (*qi, far), (*pi, far)), self.CAP)

    @staticmethod
    def _quad(buffer: BoxGeometryBuffer, corners: tuple, color: Rgb) -> None:
        buffer.add_quad(corners, (color,) * 4)

    @staticmethod
    def _ridges(span: TunnelSpan, outer: list[Point]) -> list[Point]:
        """Return the outline points that neon runs along: the roof's edges, plus a round roof's crown."""
        if span.kind is TunnelKind.SQUARE:
            return [outer[1], outer[2]]
        return [outer[1], outer[len(outer) // 2], outer[-2]]

    @staticmethod
    def _trace(positions: list[float], path: list[Point], z: float) -> None:
        for (x0, y0), (x1, y1) in pairwise(path):
            positions += (x0, y0, z, x1, y1, z)
