# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Saves and loads the brain as a JSON file."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from synthride.ai.brain import Brain

if TYPE_CHECKING:
    from pathlib import Path


class BrainStore:
    """Keeps the brain in a JSON file, written atomically so an interrupted save never corrupts it."""

    def __init__(self, path: Path) -> None:
        """Store the brain at ``path``."""
        self.path = path

    def load(self) -> Brain | None:
        """Return the stored brain, or None if there is none yet."""
        if not self.path.exists():
            return None
        return Brain.from_dict(json.loads(self.path.read_text(encoding="utf-8")))

    def save(self, brain: Brain) -> None:
        """Write ``brain``, replacing the stored one."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(brain.to_dict(), indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
