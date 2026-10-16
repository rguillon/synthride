# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""A frames-per-second meter."""

from __future__ import annotations


class FpsCounter:
    """Averages the frame rate over a short window, so the readout is steady enough to read."""

    WINDOW_SECONDS = 0.5

    def __init__(self) -> None:
        """Start with no reading."""
        self.fps: float | None = None
        self._frames = 0
        self._elapsed = 0.0

    def record(self, dt: float) -> bool:
        """Count a frame that took ``dt`` seconds; return True when a new reading is ready."""
        self._frames += 1
        self._elapsed += dt
        if self._elapsed < self.WINDOW_SECONDS:
            return False
        self.fps = self._frames / self._elapsed
        self._frames = 0
        self._elapsed = 0.0
        return True
