import math

from synthride.core.vector3 import Vector3


def test_arithmetic():
    a, b = Vector3(1, 2, 3), Vector3(4, 5, 6)
    assert a + b == Vector3(5, 7, 9)
    assert b - a == Vector3(3, 3, 3)
    assert a * 2 == Vector3(2, 4, 6)
    assert 2 * a == Vector3(2, 4, 6)


def test_length():
    assert math.isclose(Vector3(3, 4, 0).length(), 5)


def test_with_component_returns_new_vector():
    v = Vector3(1, 2, 3)
    assert v.with_x(9) == Vector3(9, 2, 3)
    assert v.with_y(9) == Vector3(1, 9, 3)
    assert v.with_z(9) == Vector3(1, 2, 9)
    assert v == Vector3(1, 2, 3)
