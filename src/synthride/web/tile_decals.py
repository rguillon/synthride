# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The animated markings on special tiles."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar

from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.web.decal_painter import DecalPainter
from synthride.web.decal_style import DecalStyle
from synthride.web.palette import Palette

if TYPE_CHECKING:
    from synthride.core.track import Track
    from synthride.web.js_bridge import JsBridge, JsObject


class TileDecals:
    """Glowing, animated markings that show what each kind of block does.

    Plain blocks carry a faint panel grid. Boost chevrons race forward, slow chevrons crawl back, pushers' arrows
    stream sideways, kill blocks flash hazard stripes, and jump pads and air blocks raise a sheet of rising arrows
    or bubbles at the front of each patch. Each layer is one mesh per tile type, mapped in track units so patterns
    run seamlessly across neighbouring tiles; animating is just sliding the texture.
    """

    DECK_LIFT = 0.006
    CURTAIN_HEIGHT = 1.3
    DECKS: ClassVar[dict[TileType, DecalStyle]] = {
        TileType.NORMAL: DecalStyle("grid", opacity=0.22),
        TileType.BOOST: DecalStyle("chevrons-up", drift=(0.0, 2.4), opacity=0.9),
        TileType.SLOW: DecalStyle("chevrons-down", drift=(0.0, -0.5), opacity=0.75),
        TileType.KILL: DecalStyle("stripes", drift=(0.5, 0.0), opacity=0.7, pulse=9.0),
        TileType.REFUEL: DecalStyle("plus", opacity=0.85, pulse=4.0),
        TileType.AIR: DecalStyle("bubbles", drift=(0.0, 0.3), opacity=0.8),
        TileType.JUMP: DecalStyle("target", opacity=0.85, pulse=6.0),
        TileType.ICE: DecalStyle("crystal", drift=(0.12, 0.04), opacity=0.5),
        TileType.PUSH_LEFT: DecalStyle("chevrons-left", drift=(-1.6, 0.0), opacity=0.85),
        TileType.PUSH_RIGHT: DecalStyle("chevrons-right", drift=(1.6, 0.0), opacity=0.85),
        TileType.FINISH: DecalStyle("checker", opacity=0.55, pulse=2.0),
    }
    CURTAINS: ClassVar[dict[TileType, DecalStyle]] = {
        TileType.JUMP: DecalStyle("chevrons-up", drift=(0.0, 1.6), opacity=0.7),
        TileType.AIR: DecalStyle("bubbles", drift=(0.0, 0.6), opacity=0.6),
    }

    def __init__(self, bridge: JsBridge, painter: DecalPainter | None = None) -> None:
        """Paint the markings with ``painter``."""
        self._bridge = bridge
        self._painter = painter or DecalPainter(bridge)
        self._layers: list[tuple[DecalStyle, JsObject, JsObject]] = []  # (style, texture, material)

    def build(self, track: Track) -> JsObject:
        """Return a group holding every marking of ``track``. Replaces (and frees) the previous one."""
        for _, texture, _ in self._layers:
            texture.dispose()
        self._layers = []
        decks: dict[TileType, list[Tile]] = {}
        curtains: dict[TileType, list[Tile]] = {}
        for tile in track.tiles():
            if tile.tile_type in self.DECKS:
                decks.setdefault(tile.tile_type, []).append(tile)
            behind = track.tile_at(tile.column, tile.row - 1)
            if tile.tile_type in self.CURTAINS and (behind is None or behind.tile_type is not tile.tile_type):
                curtains.setdefault(tile.tile_type, []).append(tile)
        group = self._bridge.three.Group.new()
        for tile_type, tiles in decks.items():
            group.add(self._layer(self.DECKS[tile_type], tile_type, [self._deck_quad(tile) for tile in tiles]))
        for tile_type, tiles in curtains.items():
            group.add(self._layer(self.CURTAINS[tile_type], tile_type, [self._curtain_quad(tile) for tile in tiles]))
        return group

    def animate(self, time: float) -> None:
        """Scroll and pulse the markings at ``time``."""
        for style, texture, material in self._layers:
            dx, dy = style.drift
            texture.offset.set(-dx * time % 1, -dy * time % 1)
            if style.pulse:
                material.opacity = style.opacity * (0.55 + 0.45 * (1 + math.sin(time * style.pulse)) / 2)

    @property
    def layer_count(self) -> int:
        """The number of marking layers built."""
        return len(self._layers)

    def _deck_quad(self, tile: Tile) -> list[tuple[float, ...]]:
        """Corners as (x, y, z, u, v, shade), in world coordinates, wound to face up and lying on the tile's top.

        The quad is drawn as two triangles split along its first diagonal, so it starts at the highest corner
        to fold along the crease of a corner slope.
        """
        corners = [(0, 0), (1, 0), (1, 1), (0, 1)]
        apex = max(range(4), key=lambda index: tile.corner_height(*corners[index]))
        quad = []
        for cx, cz in corners[apex:] + corners[:apex]:
            x, z = (tile.column + cx) * Tile.WIDTH, (tile.row + cz) * Tile.LENGTH
            quad.append((x, tile.corner_height(cx, cz) + self.DECK_LIFT, -z, x, z, 1.0))
        return quad

    def _curtain_quad(self, tile: Tile) -> list[tuple[float, ...]]:
        """Return a sheet standing across the middle of the tile, facing the camera, fading out toward its top."""
        x0, x1 = tile.column * Tile.WIDTH, (tile.column + 1) * Tile.WIDTH
        middle = (tile.row + 0.5) * Tile.LENGTH
        z = -middle
        y0 = tile.height_at((x0 + x1) / 2, middle)
        y1 = y0 + self.CURTAIN_HEIGHT
        height = self.CURTAIN_HEIGHT
        return [
            (x0, y0, z, x0, 0.0, 1.0),
            (x1, y0, z, x1, 0.0, 1.0),
            (x1, y1, z, x1, height, 0.0),
            (x0, y1, z, x0, height, 0.0),
        ]

    def _layer(self, style: DecalStyle, tile_type: TileType, quads: list[list[tuple[float, ...]]]) -> JsObject:
        three, bridge = self._bridge.three, self._bridge
        positions: list[float] = []
        uvs: list[float] = []
        shades: list[float] = []
        for quad in quads:
            for index in (0, 1, 2, 0, 2, 3):
                x, y, z, u, v, shade = quad[index]
                positions += (x, y, z)
                uvs += (u, v)
                shades += (shade, shade, shade)
        geometry = three.BufferGeometry.new()
        geometry.setAttribute("position", three.BufferAttribute.new(bridge.float32_array(positions), 3))
        geometry.setAttribute("uv", three.BufferAttribute.new(bridge.float32_array(uvs), 2))
        geometry.setAttribute("color", three.BufferAttribute.new(bridge.float32_array(shades), 3))
        texture = three.CanvasTexture.new(self._painter.canvas(style.pattern))
        texture.wrapS = texture.wrapT = three.RepeatWrapping
        texture.anisotropy = 8
        material = three.MeshBasicMaterial.new(
            bridge.obj(
                map=texture,
                color=Palette.tile_color(tile_type),
                vertexColors=True,
                transparent=True,
                opacity=style.opacity,
                blending=three.AdditiveBlending,
                depthWrite=False,
                side=three.DoubleSide,
            )
        )
        self._layers.append((style, texture, material))
        return three.Mesh.new(geometry, material)
