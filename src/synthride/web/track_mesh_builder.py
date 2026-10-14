# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The track's meshes."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar

from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3
from synthride.web.box_geometry_buffer import BoxGeometryBuffer
from synthride.web.palette import Palette
from synthride.web.tile_decals import TileDecals
from synthride.web.tunnel_mesh_builder import TunnelMeshBuilder

if TYPE_CHECKING:
    from synthride.core.track import Track
    from synthride.web.js_bridge import JsBridge, JsObject
    from synthride.web.neon_lines import NeonLines


class TrackMeshBuilder:
    """Turns a track into solid shaded slabs trimmed with neon: one mesh and one rail set per tile type.

    Tiles read as one continuous surface: a neon rail runs only along top edges that drop away (track
    borders, holes, steps down), and a faint grid marks the seams between tiles of equal height. Tunnels
    and the animated markings that explain each block are added on top.

    Game coordinates map to Three.js world coordinates as (x, y, -z), so the track runs away from the
    camera along -z.
    """

    BODY_GLOW = 0.06
    LINE_WIDTH = 2.5
    SEAM_WIDTH = 1.2
    SEAM_COLOR = Palette.mix(Palette.TILE_BODY, Palette.GRID, 0.6)
    LINE_LIFT = 0.003  # keeps lines lying on a deck from flickering against it
    DECK_TINT = 0.24  # how much of the tile colour shows on its top face
    WALL_TINT = 0.14
    WALL_FOOT = 0x05000A
    PULSING: ClassVar[dict[TileType, float]] = {
        TileType.KILL: 7.0,
        TileType.BOOST: 4.0,
        TileType.JUMP: 6.0,
        TileType.FINISH: 2.0,
    }
    # Neighbour offsets (column, row) and the top edge of a unit cell they share, as (x, z) corners.
    SIDES = (
        ((-1, 0), ((0, 0), (0, 1))),
        ((1, 0), ((1, 0), (1, 1))),
        ((0, -1), ((0, 0), (1, 0))),
        ((0, 1), ((0, 1), (1, 1))),
    )

    def __init__(
        self,
        bridge: JsBridge,
        lines: NeonLines,
        tunnels: TunnelMeshBuilder | None = None,
        decals: TileDecals | None = None,
    ) -> None:
        """Build tunnels with ``tunnels`` and markings with ``decals``."""
        self._bridge = bridge
        self._lines = lines
        self._tunnels = tunnels or TunnelMeshBuilder(bridge, lines)
        self._decals = decals or TileDecals(bridge)
        self._materials: dict[TileType, JsObject] = {}
        self._outlines: list[JsObject] = []

    def build(self, track: Track) -> JsObject:
        """Return a group holding every mesh of ``track``."""
        three = self._bridge.three
        buffers: dict[TileType, BoxGeometryBuffer] = {}
        rails: dict[TileType, list[float]] = {}
        seams: list[float] = []
        for tile in track.tiles():
            box = tile.bounding_box
            color = Palette.tile_color(tile.tile_type)
            buffers.setdefault(tile.tile_type, BoxGeometryBuffer()).add_box(
                Vector3(box.minimum.x, 0.0, -box.maximum.z),
                Vector3(box.maximum.x, box.maximum.y, -box.minimum.z),
                top_color=Palette.linear_rgb(Palette.mix(Palette.TILE_BODY, color, self.DECK_TINT)),
                wall_upper=Palette.linear_rgb(Palette.mix(Palette.TILE_BODY, color, self.WALL_TINT)),
                wall_lower=Palette.linear_rgb(self.WALL_FOOT),
            )
            self._trace_edges(track, tile, rails.setdefault(tile.tile_type, []), seams)
        group = three.Group.new()
        self._materials = {}
        for outline in self._outlines:
            self._lines.release(outline)
        self._outlines = []
        for tile_type, buffer in buffers.items():
            color = Palette.tile_color(tile_type)
            material = three.MeshStandardMaterial.new(
                self._bridge.obj(
                    vertexColors=True,
                    emissive=color,
                    emissiveIntensity=self.BODY_GLOW,
                    roughness=0.55,
                    metalness=0.2,
                )
            )
            self._materials[tile_type] = material
            surfaces = three.BufferGeometry.new()
            surfaces.setAttribute("position", self._attribute(buffer.positions))
            surfaces.setAttribute("normal", self._attribute(buffer.normals))
            surfaces.setAttribute("color", self._attribute(buffer.colors))
            group.add(three.Mesh.new(surfaces, material))
            if rails[tile_type]:
                self._add_lines(group, rails[tile_type], color, self.LINE_WIDTH)
        if seams:
            self._add_lines(group, seams, self.SEAM_COLOR, self.SEAM_WIDTH)
        group.add(self._decals.build(track))
        for part in self._tunnels.build(track):
            if part in self._lines:
                self._outlines.append(part)
            group.add(part)
        return group

    def _trace_edges(self, track: Track, tile: Tile, rails: list[float], seams: list[float]) -> None:
        """Add a rail on each top edge that drops away, and a seam (owned by one side) toward an equal neighbour."""
        y = tile.top + self.LINE_LIFT
        for (dc, dr), corners in self.SIDES:
            neighbour = track.tile_at(tile.column + dc, tile.row + dr)
            if neighbour is None or neighbour.top < tile.top:
                target = rails
            elif neighbour.top == tile.top and dc + dr > 0:
                target = seams
            else:
                continue
            for cx, cz in corners:
                target.extend(((tile.column + cx) * Tile.SIZE, y, -(tile.row + cz) * Tile.SIZE))

    def _add_lines(self, group: JsObject, positions: list[float], color: int, width: float) -> None:
        line = self._lines.segments(positions, color, width)
        self._outlines.append(line)
        group.add(line)

    def animate(self, time: float) -> None:
        """Make dangerous and special tiles throb, and their markings move."""
        self._decals.animate(time)
        for tile_type, frequency in self.PULSING.items():
            material = self._materials.get(tile_type)
            if material is not None:
                material.emissiveIntensity = self.BODY_GLOW + 0.25 * (1 + math.sin(time * frequency)) / 2

    def _attribute(self, values: list[float]) -> JsObject:
        return self._bridge.three.BufferAttribute.new(self._bridge.float32_array(values), 3)
