# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The folder of level files that the dev server saves the editor's tracks into."""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from synthride.core.level_parser import LevelParser


class LevelFolder:
    """Writes level files sent by the editor into the levels package, checking each one first."""

    NAME: ClassVar[re.Pattern[str]] = re.compile(r"level_\d{2,}\.json")
    MAX_BYTES: ClassVar[int] = 2_000_000

    def __init__(self, root: Path | None = None) -> None:
        """Save into ``root``, by default the bundled levels package."""
        self.root = root or Path(__file__).resolve().parent.parent / "levels"

    def save(self, name: str, text: str) -> Path:
        """Write the level file ``text`` as ``name`` and return its path.

        Raise ``ValueError`` if ``name`` is not a level file name, such as ``level_07.json``, or ``text`` is not a
        level file.
        """
        if not self.NAME.fullmatch(name):
            msg = f"not a level file name: {name!r}"
            raise ValueError(msg)
        LevelParser().parse(text)
        path = self.root / name
        path.write_text(text if text.endswith("\n") else f"{text}\n", encoding="utf-8")
        return path
