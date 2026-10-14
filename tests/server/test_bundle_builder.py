# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import io
import zipfile
from pathlib import Path

from synthride.server.bundle_builder import BundleBuilder


def make_package(tmp_path: Path) -> Path:
    root = tmp_path / "synthride"
    for relative in ("__init__.py", "core/a.py", "web/b.py", "levels/l.py", "server/s.py", "core/__pycache__/x.py"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative)
    (root / "core" / "notes.md").write_text("ignored")
    return root


def test_bundles_only_client_files(tmp_path: Path) -> None:
    names = [path.as_posix() for path in BundleBuilder(make_package(tmp_path)).files()]
    assert names == ["synthride/__init__.py", "synthride/core/a.py", "synthride/web/b.py", "synthride/levels/l.py"]


def test_build_produces_a_deterministic_zip(tmp_path: Path) -> None:
    builder = BundleBuilder(make_package(tmp_path))
    data = builder.build()
    assert data == builder.build()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.read("synthride/core/a.py") == b"core/a.py"


def test_default_root_bundles_the_real_game() -> None:
    names = {path.as_posix() for path in BundleBuilder().files()}
    assert "synthride/core/game_session.py" in names
    assert "synthride/web/main.py" in names
    assert "synthride/levels/level_01.py" in names
    assert not any(name.startswith("synthride/server") for name in names)
