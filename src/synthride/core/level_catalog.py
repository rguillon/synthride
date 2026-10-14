# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Discovery and loading of the bundled level files."""

from __future__ import annotations

from importlib import resources
from typing import TYPE_CHECKING

from synthride.core.level_parser import LevelParser

if TYPE_CHECKING:
    from synthride.core.level import Level


class LevelCatalog:
    """Finds and loads the level files bundled in a package, in file-name order."""

    SUFFIX = ".json"

    def __init__(self, package: str = "synthride.levels", parser: LevelParser | None = None) -> None:
        """Look for levels in ``package``, parsing them with ``parser``."""
        self._package = package
        self._parser = parser or LevelParser()

    def file_names(self) -> list[str]:
        """Return the names of the level files, sorted."""
        root = resources.files(self._package)
        return sorted(entry.name for entry in root.iterdir() if entry.name.endswith(self.SUFFIX))

    def load(self, file_name: str) -> Level:
        """Load and parse one level file."""
        text = resources.files(self._package).joinpath(file_name).read_text(encoding="utf-8")
        return self._parser.parse(text)

    def load_all(self) -> list[Level]:
        """Load every level, in file-name order."""
        return [self.load(file_name) for file_name in self.file_names()]
