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
    from synthride.web.ship_reflection import ShipReflection


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
    # Kill patches are ringed where they meet safe ground too, in the track border's colour but a thinner line.
    KILL_OUTLINE_WIDTH = 1.8
    KILL_OUTLINE_COLOR = Palette.tile_color(TileType.NORMAL)
    # Rails take their tile's colour, except where that would draw a red line: kill tiles are bordered like the track.
    RAIL_COLORS: ClassVar[dict[TileType, int]] = {TileType.KILL: KILL_OUTLINE_COLOR}
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
        reflection: ShipReflection | None = None,
    ) -> None:
        """Build tunnels with ``tunnels`` and markings with ``decals``; decks show ``reflection``, if any."""
        self._bridge = bridge
        self._reflection = reflection
        self._lines = lines
        self._tunnels = tunnels or TunnelMeshBuilder(bridge, lines)
        self._decals = decals or TileDecals(bridge)
        self._materials: dict[TileType, JsObject] = {}
        self._outlines: list[JsObject] = []

    def build(self, track: Track) -> JsObject:
        """Return a group holding every mesh of ``track``."""
        three = self._bridge.three
        buffers: dict[TileType, BoxGeometryBuffer] = {}
        rails: dict[int, list[float]] = {}  # by colour
        seams: list[float] = []
        kill_outline: list[float] = []
        shades: dict[TileType, dict[str, tuple[float, float, float]]] = {}
        corners: dict[tuple[int, int], dict[tuple[int, int], float]] = {}
        for tile in track.tiles():
            box = tile.bounding_box
            minimum = Vector3(box.minimum.x, 0.0, -box.maximum.z)
            maximum = Vector3(box.maximum.x, box.maximum.y, -box.minimum.z)
            if tile.tile_type not in shades:
                shades[tile.tile_type] = self._shades(tile.tile_type)
            colors = shades[tile.tile_type]
            buffer = buffers.setdefault(tile.tile_type, BoxGeometryBuffer())
            if tile.slope is None:
                buffer.add_box(minimum, maximum, **colors)
            else:
                # World z runs backward, so the world corners (x0, z0)... are the game corners (0, 1), (1, 1)...
                corner = tile.corner_height
                heights = (corner(0, 1), corner(1, 1), corner(1, 0), corner(0, 0))
                buffer.add_sloped_box(minimum, maximum, heights, **colors)
            rail_color = self.RAIL_COLORS.get(tile.tile_type, Palette.tile_color(tile.tile_type))
            targets = (rails.setdefault(rail_color, []), seams, kill_outline)
            self._trace_edges(track, tile, targets, corners)
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
                    # Far away, depth precision gets coarser than LINE_LIFT: push the slabs back so lines stay on top.
                    polygonOffset=True,
                    polygonOffsetFactor=1,
                    polygonOffsetUnits=4,
                )
            )
            if self._reflection is not None:
                self._reflection.patch(material)
            self._materials[tile_type] = material
            surfaces = three.BufferGeometry.new()
            surfaces.setAttribute("position", self._attribute(buffer.positions))
            surfaces.setAttribute("normal", self._attribute(buffer.normals))
            surfaces.setAttribute("color", self._attribute(buffer.colors))
            group.add(three.Mesh.new(surfaces, material))
        for color, positions in rails.items():
            self._add_lines(group, positions, color, self.LINE_WIDTH)
        self._add_lines(group, seams, self.SEAM_COLOR, self.SEAM_WIDTH)  # never empty: every tile has a middle seam
        self._add_lines(group, kill_outline, self.KILL_OUTLINE_COLOR, self.KILL_OUTLINE_WIDTH)
        group.add(self._decals.build(track))
        for part in self._tunnels.build(track):
            if part in self._lines:
                self._outlines.append(part)
            group.add(part)
        return group

    def _shades(self, tile_type: TileType) -> dict[str, tuple[float, float, float]]:
        """Return the vertex colours of a tile of ``tile_type``: its top, and its walls from top edge to foot."""
        color = Palette.tile_color(tile_type)
        return {
            "top_color": Palette.linear_rgb(Palette.mix(Palette.TILE_BODY, color, self.DECK_TINT)),
            "wall_upper": Palette.linear_rgb(Palette.mix(Palette.TILE_BODY, color, self.WALL_TINT)),
            "wall_lower": Palette.linear_rgb(self.WALL_FOOT),
        }

    @staticmethod
    def _corners(
        tile: Tile, cache: dict[tuple[int, int], dict[tuple[int, int], float]]
    ) -> dict[tuple[int, int], float]:
        """Return the heights of ``tile``'s top corners, by (x, z) corner, worked out once per tile in ``cache``."""
        key = (tile.column, tile.row)
        if key not in cache:
            cache[key] = {(cx, cz): tile.corner_height(cx, cz) for cx in (0, 1) for cz in (0, 1)}
        return cache[key]

    def _trace_edges(
        self,
        track: Track,
        tile: Tile,
        targets: tuple[list[float], list[float], list[float]],
        cache: dict[tuple[int, int], dict[tuple[int, int], float]],
    ) -> None:
        """Add a rail on each top edge that drops away, and a seam (owned by one side) toward an equal neighbour.

        Edges are compared corner by corner, so slopes join flat tiles and other slopes seamlessly. A seam also
        splits each tile into two squares across its middle, and a corner slope gets one along its crease.
        ``targets`` are the rails, the seams and the kill outline, which takes a kill tile's other edges
        toward any tile of another type, in place of their seam.
        """
        rails, seams, kill_outline = targets
        killing = tile.tile_type is TileType.KILL
        heights = self._corners(tile, cache)
        for (dc, dr), corners in self.SIDES:
            neighbour = track.tile_at(tile.column + dc, tile.row + dr)
            mine = [heights[corner] for corner in corners]
            if neighbour is None:
                theirs = None
            else:
                across = self._corners(neighbour, cache)
                theirs = [across[cx - dc, cz - dr] for cx, cz in corners]
            if theirs is None or any(t < m for t, m in zip(theirs, mine, strict=True)):
                target = rails
            elif neighbour is not None and killing != (neighbour.tile_type is TileType.KILL):
                if not killing:
                    continue
                target = kill_outline
            elif theirs == mine and dc + dr > 0:
                target = seams
            else:
                continue
            self._add_edge(tile, corners, target)
        corner_slope = tile.slope is not None and all(tile.slope.direction)
        # A corner slope folds in the middle of that seam.
        middle = ((0, 0.5), (0.5, 0.5), (0.5, 0.5), (1, 0.5)) if corner_slope else ((0, 0.5), (1, 0.5))
        self._add_edge(tile, middle, seams)
        if corner_slope:
            dx, dz = tile.slope.direction
            self._add_edge(tile, ((0, 0), (1, 1)) if dx == dz else ((1, 0), (0, 1)), seams)

    def _add_edge(self, tile: Tile, corners: tuple[tuple[float, float], ...], target: list[float]) -> None:
        column, row, flat = tile.column, tile.row, tile.slope is None
        lift = tile.base + self.LINE_LIFT
        for cx, cz in corners:
            y = lift if flat else tile.corner_height(cx, cz) + self.LINE_LIFT
            target += ((column + cx) * Tile.WIDTH, y, -(row + cz) * Tile.LENGTH)

    def _add_lines(self, group: JsObject, positions: list[float], color: int, width: float) -> None:
        """Add a line set of ``positions`` to ``group``, unless there is nothing to draw."""
        if not positions:
            return
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
