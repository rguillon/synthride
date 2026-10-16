# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.editor.track_grid import TrackGrid
from synthride.editor.track_picker import TrackPicker

DOWN = (0.0, -1.0, 0.0)


def test_a_ray_straight_down_picks_the_tile_under_it() -> None:
    grid = TrackGrid.starter()
    assert TrackPicker.pick(grid, (3.5, 10.0, -5.0), DOWN, 1) == (3, 2)


def test_a_slanted_ray_stops_at_the_first_raised_tile() -> None:
    grid = TrackGrid([
        [None] * 8,
        [None, None, None, "N4", None, None, None, None],
        [None, None, None, "N1", *[None] * 4],
    ])
    # Looking down the track from above row 0, the ray passes over the tall tile at row 1 at height 2.
    origin, direction = (3.5, 4.0, 0.0), (0.0, -1.0, -1.0)
    assert TrackPicker.pick(grid, origin, direction, 1) == (3, 1)


def test_over_gaps_the_ray_points_at_the_brush_height() -> None:
    grid = TrackGrid()
    assert TrackPicker.pick(grid, (2.5, 5.0, -21.0), DOWN, 3) == (2, 10)


def test_rays_beside_the_track_or_upward_miss_unless_clamped() -> None:
    grid = TrackGrid()
    assert TrackPicker.pick(grid, (-3.0, 5.0, -1.0), DOWN, 1) is None
    assert TrackPicker.pick(grid, (-3.0, 5.0, 1.0), DOWN, 1, clamp=True) == (0, 0)
    assert TrackPicker.pick(grid, (12.0, 5.0, -1.0), DOWN, 1, clamp=True) == (7, 0)
    assert TrackPicker.pick(grid, (3.0, 5.0, 0.0), (0.0, 1.0, 0.0), 1) is None
    assert TrackPicker.pick(grid, (3.0, 0.1, 0.0), DOWN, 1) is None
