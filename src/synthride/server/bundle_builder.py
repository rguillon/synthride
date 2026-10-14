# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Packaging of the client-side Python code for Pyodide."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path


class BundleBuilder:
    """Zips the client side of the game (core, web and levels) for Pyodide to unpack in the browser."""

    CLIENT_PACKAGES = ("core", "web", "levels")
    SUFFIXES = frozenset({".py"})
    TIMESTAMP = (2024, 1, 1, 0, 0, 0)

    def __init__(self, package_root: Path | None = None) -> None:
        """Bundle the package found at ``package_root``, by default this one."""
        self._package_root = package_root or Path(__file__).resolve().parent.parent

    def files(self) -> list[Path]:
        """Return the paths to bundle, relative to the directory that contains the package."""
        root = self._package_root
        candidates = [root / "__init__.py"]
        for package in self.CLIENT_PACKAGES:
            candidates.extend(sorted((root / package).rglob("*")))
        return [
            path.relative_to(root.parent)
            for path in candidates
            if path.is_file() and path.suffix in self.SUFFIXES and "__pycache__" not in path.parts
        ]

    def build(self) -> bytes:
        """Return the zip archive of the client files."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for relative in self.files():
                info = zipfile.ZipInfo(relative.as_posix(), self.TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, (self._package_root.parent / relative).read_bytes())
        return buffer.getvalue()
