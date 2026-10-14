# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Thick neon line sets kept sized to the viewport."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from synthride.web.js_bridge import JsBridge, JsObject


class NeonLines:
    """Builds thick, antialiased line sets (Three.js "fat lines") and keeps them sized to the viewport.

    Plain WebGL lines are always one pixel wide. Fat lines are drawn as screen-space quads, whose width
    is given in CSS pixels, so every line material needs the current viewport resolution.
    """

    def __init__(self, bridge: JsBridge) -> None:
        """Create lines with the bridge's Three.js."""
        self._bridge = bridge
        self._lines: list[tuple[JsObject, JsObject]] = []  # (line, its material)
        self._size = (1, 1)

    def segments(self, positions: Sequence[float], color: int, width: float) -> JsObject:
        """Line segments from a flat list of start/end points: x0, y0, z0, x1, y1, z1, ..."""
        geometry = self._bridge.three.LineSegmentsGeometry.new()
        geometry.setPositions(self._bridge.float32_array(positions))
        return self._line(geometry, color, width)

    def edges_of(self, geometry: JsObject, color: int, width: float) -> JsObject:
        """Return the hard edges of a mesh geometry."""
        three = self._bridge.three
        outline = three.LineSegmentsGeometry.new()
        outline.fromEdgesGeometry(three.EdgesGeometry.new(geometry))
        return self._line(outline, color, width)

    def release(self, line: JsObject) -> None:
        """Stop resizing a line that left the scene."""
        self._lines = [(kept, material) for kept, material in self._lines if kept is not line]

    def resize(self, width: int, height: int) -> None:
        """Update every line to a viewport of ``width`` by ``height`` pixels."""
        self._size = (width, height)
        for _, material in self._lines:
            material.resolution.set(width, height)

    def __contains__(self, line: JsObject) -> bool:
        """Return whether ``line`` is still kept sized."""
        return any(kept is line for kept, _ in self._lines)

    @property
    def count(self) -> int:
        """The number of lines kept sized."""
        return len(self._lines)

    def _line(self, geometry: JsObject, color: int, width: float) -> JsObject:
        three = self._bridge.three
        material = three.LineMaterial.new(self._bridge.obj(color=color, linewidth=width, alphaToCoverage=True))
        material.resolution.set(*self._size)
        line = three.LineSegments2.new(geometry, material)
        self._lines.append((line, material))
        return line
