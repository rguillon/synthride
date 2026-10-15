# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Packaging of the game with the neural network player for Pyodide."""

from __future__ import annotations

from pathlib import Path

from synthride.server.bundle_builder import BundleBuilder


class AiBundleBuilder(BundleBuilder):
    """Bundles the client side of the game, the AI package and the brain, read afresh on every build."""

    ROOT = Path(__file__).resolve().parents[2]
    BRAIN_NAME = "data/brain.json"

    def __init__(self, brain: Path) -> None:
        """Bundle the brain stored at ``brain``."""
        super().__init__()
        self._brain = brain

    def entries(self) -> list[tuple[str, bytes]]:
        """Return the game's entries followed by the AI modules and the brain."""
        modules = [self.ROOT / "tests" / "__init__.py", *sorted((self.ROOT / "tests" / "ai").glob("*.py"))]
        return [
            *super().entries(),
            *((path.relative_to(self.ROOT).as_posix(), path.read_bytes()) for path in modules),
            (self.BRAIN_NAME, self._brain.read_bytes()),
        ]
