from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from synthride.web.js_bridge import JsBridge


class NeonLines:
    """Builds thick, antialiased line sets (Three.js "fat lines") and keeps them sized to the viewport.

    Plain WebGL lines are always one pixel wide. Fat lines are drawn as screen-space quads, whose width
    is given in CSS pixels, so every line material needs the current viewport resolution.
    """

    def __init__(self, bridge: JsBridge) -> None:
        self._bridge = bridge
        self._lines: list[tuple[Any, Any]] = []  # (line, its material)
        self._size = (1, 1)

    def segments(self, positions: Sequence[float], color: int, width: float) -> Any:
        """Line segments from a flat list of start/end points: x0, y0, z0, x1, y1, z1, ..."""
        geometry = self._bridge.three.LineSegmentsGeometry.new()
        geometry.setPositions(self._bridge.float32_array(positions))
        return self._line(geometry, color, width)

    def edges_of(self, geometry: Any, color: int, width: float) -> Any:
        """The hard edges of a mesh geometry."""
        three = self._bridge.three
        outline = three.LineSegmentsGeometry.new()
        outline.fromEdgesGeometry(three.EdgesGeometry.new(geometry))
        return self._line(outline, color, width)

    def release(self, line: Any) -> None:
        """Stops resizing a line that left the scene."""
        self._lines = [(kept, material) for kept, material in self._lines if kept is not line]

    def resize(self, width: int, height: int) -> None:
        self._size = (width, height)
        for _, material in self._lines:
            material.resolution.set(width, height)

    def __contains__(self, line: Any) -> bool:
        return any(kept is line for kept, _ in self._lines)

    @property
    def count(self) -> int:
        return len(self._lines)

    def _line(self, geometry: Any, color: int, width: float) -> Any:
        three = self._bridge.three
        material = three.LineMaterial.new(self._bridge.obj(color=color, linewidth=width, alphaToCoverage=True))
        material.resolution.set(*self._size)
        line = three.LineSegments2.new(geometry, material)
        self._lines.append((line, material))
        return line
