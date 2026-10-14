# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from collections.abc import Iterator, Sequence

from synthride.core.vector3 import Vector3
from synthride.web.box_geometry_buffer import BoxGeometryBuffer


def triangles(buffer: BoxGeometryBuffer) -> Iterator[tuple[list[tuple[float, ...]], tuple[float, ...]]]:
    points = [tuple(buffer.positions[i : i + 3]) for i in range(0, len(buffer.positions), 3)]
    normals = [tuple(buffer.normals[i : i + 3]) for i in range(0, len(buffer.normals), 3)]
    for index in range(0, len(points), 3):
        yield points[index : index + 3], normals[index]


def cross(u: Sequence[float], v: Sequence[float]) -> tuple[float, float, float]:
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def test_five_faces_two_triangles_each() -> None:
    buffer = BoxGeometryBuffer()
    buffer.add_box(Vector3(0, 0, 0), Vector3(1, 2, 3))
    assert buffer.vertex_count == 30
    assert len(buffer.normals) == len(buffer.positions)
    assert buffer.box_count == 1


def test_triangles_are_wound_counter_clockwise_toward_their_normal() -> None:
    buffer = BoxGeometryBuffer()
    buffer.add_box(Vector3(0, 0, 0), Vector3(1, 2, 3))
    for (a, b, c), normal in triangles(buffer):
        face_normal = cross(
            tuple(q - p for p, q in zip(a, b, strict=True)), tuple(q - p for p, q in zip(a, c, strict=True))
        )
        assert sum(n * f for n, f in zip(normal, face_normal, strict=True)) > 0


def test_top_face_and_walls_take_their_own_colours() -> None:
    buffer = BoxGeometryBuffer()
    top, upper, lower = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    buffer.add_box(Vector3(0, 0, 0), Vector3(1, 2, 3), top, upper, lower)
    assert len(buffer.colors) == len(buffer.positions)
    for index in range(buffer.vertex_count):
        y, normal_y = buffer.positions[index * 3 + 1], buffer.normals[index * 3 + 1]
        expected = top if normal_y else (upper if y == 2 else lower)
        assert tuple(buffer.colors[index * 3 : index * 3 + 3]) == expected


def test_boxes_accumulate() -> None:
    buffer = BoxGeometryBuffer()
    buffer.add_box(Vector3(0, 0, 0), Vector3(1, 1, 1))
    buffer.add_box(Vector3(1, 0, 0), Vector3(2, 1, 1))
    assert buffer.vertex_count == 60
    assert buffer.box_count == 2


def test_quad_normal_follows_its_winding() -> None:
    buffer = BoxGeometryBuffer()
    red = (1.0, 0.0, 0.0)
    buffer.add_quad(((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), (red,) * 4)
    assert buffer.vertex_count == 6
    assert buffer.normals[:3] == [0.0, 0.0, 1.0]
    assert buffer.colors[:3] == list(red)


def test_sloped_box_has_four_walls_and_a_top_folded_along_its_highest_corner() -> None:
    buffer = BoxGeometryBuffer()
    buffer.add_sloped_box(Vector3(0, 0, 0), Vector3(1, 0, 1), (1.0, 1.0, 2.0, 1.0))
    assert buffer.vertex_count == 4 * 6 + 2 * 3
    assert buffer.box_count == 1
    top = [tuple(buffer.positions[i : i + 3]) for i in range(24 * 3, 30 * 3, 3)]
    assert top[0] == top[3] == (1, 2.0, 1)  # both triangles start at the raised corner
    for (a, b, c), normal in triangles(buffer):
        face_normal = cross(
            tuple(q - p for p, q in zip(a, b, strict=True)), tuple(q - p for p, q in zip(a, c, strict=True))
        )
        assert sum(n * f for n, f in zip(normal, face_normal, strict=True)) > 0
    assert all(normal[1] > 0 for _, normal in list(triangles(buffer))[-2:])


def test_sloped_walls_fade_from_their_top_edge_to_their_foot() -> None:
    buffer = BoxGeometryBuffer()
    top, upper, lower = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    buffer.add_sloped_box(
        Vector3(0, 0, 0), Vector3(1, 0, 1), (1.0, 1.5, 1.5, 1.0), top_color=top, wall_upper=upper, wall_lower=lower
    )
    for index in range(buffer.vertex_count):
        y, normal_y = buffer.positions[index * 3 + 1], buffer.normals[index * 3 + 1]
        expected = top if normal_y > 0 else (lower if y == 0 else upper)
        assert tuple(buffer.colors[index * 3 : index * 3 + 3]) == expected
