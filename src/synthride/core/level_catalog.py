# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Discovery and loading of the bundled level modules."""

from __future__ import annotations

import importlib
from importlib import resources

from synthride.core.level import Level


class LevelCatalog:
    """Finds and loads the level modules bundled in a package, in module-name order.

    A level module is named ``level_*.py`` and defines a ``LEVEL`` constant holding its :class:`Level`.
    """

    PREFIX = "level_"
    SUFFIX = ".py"
    ATTRIBUTE = "LEVEL"

    def __init__(self, package: str = "synthride.levels") -> None:
        """Look for levels in ``package``."""
        self._package = package

    def module_names(self) -> list[str]:
        """Return the names of the level modules, sorted."""
        root = resources.files(self._package)
        return sorted(
            entry.name.removesuffix(self.SUFFIX)
            for entry in root.iterdir()
            if entry.name.startswith(self.PREFIX) and entry.name.endswith(self.SUFFIX)
        )

    def load(self, module_name: str) -> Level:
        """Import one level module and return its level."""
        level = getattr(importlib.import_module(f"{self._package}.{module_name}"), self.ATTRIBUTE, None)
        if not isinstance(level, Level):
            message = f"{self._package}.{module_name} must define {self.ATTRIBUTE} as a Level"
            raise TypeError(message)
        return level

    def load_all(self) -> list[Level]:
        """Load every level, in module-name order."""
        return [self.load(module_name) for module_name in self.module_names()]
