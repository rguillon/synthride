from __future__ import annotations

from importlib import resources

from synthride.core.level import Level
from synthride.core.level_parser import LevelParser


class LevelCatalog:
    """Finds and loads the level files bundled in a package, in file-name order."""

    SUFFIX = ".txt"

    def __init__(self, package: str = "synthride.levels", parser: LevelParser | None = None) -> None:
        self._package = package
        self._parser = parser or LevelParser()

    def file_names(self) -> list[str]:
        root = resources.files(self._package)
        return sorted(entry.name for entry in root.iterdir() if entry.name.endswith(self.SUFFIX))

    def load(self, file_name: str) -> Level:
        text = resources.files(self._package).joinpath(file_name).read_text(encoding="utf-8")
        return self._parser.parse(text)

    def load_all(self) -> list[Level]:
        return [self.load(file_name) for file_name in self.file_names()]
