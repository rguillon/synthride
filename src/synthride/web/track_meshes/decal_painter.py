# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Painting of the tile marking patterns."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from synthride.web.browser.js_bridge import JsBridge, JsObject


class DecalPainter:
    """Paints the white, tileable patterns that mark what a block does, on 2D canvases.

    One canvas covers one tile. Its top edge points forward along the track (or up, on a vertical sheet).
    Every pattern stays clear of the canvas edges or wraps around them, so it tiles without seams.
    """

    SIZE = 128
    TURNS: ClassVar[dict[str, float]] = {"up": 0.0, "right": math.pi / 2, "down": math.pi, "left": -math.pi / 2}
    BUBBLES = ((34, 30, 14), (92, 22, 8), (86, 80, 18), (30, 96, 9), (60, 58, 5))

    def __init__(self, bridge: JsBridge) -> None:
        """Paint on canvases created in the bridge's document."""
        self._document = bridge.document
        self._canvases: dict[str, JsObject] = {}

    def canvas(self, pattern: str) -> JsObject:
        """Return the canvas painted with ``pattern``, painting it on first use.

        ``pattern`` is ``chevrons-<up|down|left|right>``, ``stripes``, ``plus``, ``bubbles``, ``target``,
        ``crystal``, ``checker`` or ``grid``. Canvases are painted once and shared.
        """
        if pattern not in self._canvases:
            canvas = self._document.createElement("canvas")
            canvas.width = canvas.height = self.SIZE
            context = canvas.getContext("2d")
            context.strokeStyle = context.fillStyle = "#ffffff"
            context.lineCap = context.lineJoin = "round"
            name, _, direction = pattern.partition("-")
            getattr(self, f"_paint_{name}")(context, *([direction] if direction else []))
            self._canvases[pattern] = canvas
        return self._canvases[pattern]

    def _paint_chevrons(self, context: JsObject, direction: str) -> None:
        middle = self.SIZE / 2
        context.translate(middle, middle)
        context.rotate(self.TURNS[direction])
        context.translate(-middle, -middle)
        context.lineWidth = 12
        for tip in (18, 82):
            self._polyline(context, ((22, tip + 26), (64, tip), (106, tip + 26)))

    def _paint_stripes(self, context: JsObject) -> None:
        context.lineWidth = 11
        context.lineCap = "butt"
        for start in range(-self.SIZE, 2 * self.SIZE, 32):
            self._polyline(context, ((start, -8), (start + self.SIZE + 16, self.SIZE + 8)))

    def _paint_plus(self, context: JsObject) -> None:
        context.lineWidth = 16
        self._polyline(context, ((64, 30), (64, 98)))
        self._polyline(context, ((30, 64), (98, 64)))

    def _paint_bubbles(self, context: JsObject) -> None:
        context.lineWidth = 5
        for x, y, radius in self.BUBBLES:
            context.beginPath()
            context.arc(x, y, radius, 0, 2 * math.pi)
            context.stroke()

    def _paint_target(self, context: JsObject) -> None:
        context.lineWidth = 8
        context.strokeRect(18, 18, 92, 92)
        context.strokeRect(42, 42, 44, 44)
        context.fillRect(58, 58, 12, 12)

    def _paint_crystal(self, context: JsObject) -> None:
        context.lineWidth = 5
        for step in range(3):
            angle = step * math.pi / 3
            dx, dy = 30 * math.cos(angle), 30 * math.sin(angle)
            self._polyline(context, ((64 - dx, 64 - dy), (64 + dx, 64 + dy)))
        context.lineWidth = 3
        for x, y in ((16, 26), (100, 104), (104, 20)):
            self._polyline(context, ((x, y + 10), (x + 10, y)))

    def _paint_checker(self, context: JsObject) -> None:
        cell = self.SIZE // 4
        for row in range(4):
            for column in range(row % 2, 4, 2):
                context.fillRect(column * cell, row * cell, cell, cell)

    def _paint_grid(self, context: JsObject) -> None:
        cell = self.SIZE // 4
        context.lineWidth = 2
        context.lineCap = "butt"
        # Lines on the canvas edges are drawn on both sides, so each half meets its wrapped twin.
        for offset in range(0, self.SIZE + 1, cell):
            self._polyline(context, ((offset, 0), (offset, self.SIZE)))
            self._polyline(context, ((0, offset), (self.SIZE, offset)))
        for row in range(4):
            for column in range(4):
                x, y = column * cell + cell // 2, row * cell + cell // 2
                context.fillRect(x - 2, y - 2, 4, 4)

    @staticmethod
    def _polyline(context: JsObject, points: tuple[tuple[float, float], ...]) -> None:
        context.beginPath()
        context.moveTo(*points[0])
        for point in points[1:]:
            context.lineTo(*point)
        context.stroke()
