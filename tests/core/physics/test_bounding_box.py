# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.physics.bounding_box import BoundingBox
from synthride.core.physics.vector3 import Vector3


def test_from_bottom_center() -> None:
    box = BoundingBox.from_bottom_center(Vector3(1, 2, 3), width=2, height=1, length=4)
    assert box.minimum == Vector3(0, 2, 1)
    assert box.maximum == Vector3(2, 3, 5)
    assert box.center_x == 1


def test_overlaps() -> None:
    a = BoundingBox(Vector3(0, 0, 0), Vector3(2, 1, 2))
    b = BoundingBox(Vector3(1.5, 5, 1), Vector3(3, 6, 3))
    assert a.overlap_x(b) == pytest.approx(0.5)
    assert a.overlap_z(b) == pytest.approx(1)
    assert a.overlaps_footprint(b)


def test_touching_boxes_do_not_overlap() -> None:
    a = BoundingBox(Vector3(0, 0, 0), Vector3(1, 1, 1))
    b = BoundingBox(Vector3(1, 0, 0), Vector3(2, 1, 1))
    assert a.overlap_x(b) == 0
    assert not a.overlaps_footprint(b)
