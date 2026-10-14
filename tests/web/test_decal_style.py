# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.web.decal_style import DecalStyle


def test_defaults_are_a_steady_still_glow() -> None:
    style = DecalStyle("plus")
    assert (style.drift, style.pulse) == ((0.0, 0.0), 0.0)
