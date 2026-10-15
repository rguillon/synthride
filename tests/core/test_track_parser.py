# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.slope import Slope
from synthride.core.tile_type import TileType
from synthride.core.track_parser import TrackFormatError, TrackParser
from synthride.core.tunnel_kind import TunnelKind

ROW = ".. " * 8


def test_parses_rows() -> None:
    track = TrackParser().parse([(1, ".. .. N1 N1 N1 N1 .. .."), (1, "B2 S3 K4 R1 F1 N1 .. ..")])
    assert track.row_count == 2
    assert track.tile_at(0, 0) is None
    boost = track.tile_at(0, 1)
    assert boost is not None
    assert (boost.tile_type, boost.level, boost.row, boost.column) == (TileType.BOOST, 2, 1, 0)
    kill = track.tile_at(2, 1)
    assert kill is not None
    assert kill.tile_type is TileType.KILL


def test_repeats_a_row_count_times() -> None:
    track = TrackParser().parse([(3, "N1 " * 8), (2, ROW), (1, "B1 " * 8)])
    assert track.row_count == 6
    assert [track.tile_at(0, row) is not None for row in range(6)] == [True, True, True, False, False, True]
    third = track.tile_at(4, 2)
    assert third is not None
    assert (third.row, third.column) == (2, 4)
    last = track.tile_at(0, 5)
    assert last is not None
    assert last.tile_type is TileType.BOOST


@pytest.mark.parametrize(
    ("rows", "location"),
    [
        ([], "track"),
        ([ROW], "row[0]"),
        ([(1, ROW), (1, ROW, 2)], "row[1]"),
        ([(0, ROW)], "row[0]"),
        ([(-2, ROW)], "row[0]"),
        ([(True, ROW)], "row[0]"),
        ([(1.5, ROW)], "row[0]"),
        ([(1, 8)], "row[0]"),
        ([(1, ".. ..")], "row[0]"),
        ([(1, ROW), (4, ROW), (1, ".. " * 7 + "X1")], "row[2]"),
        ([(1, ".. " * 7 + "N9")], "row[0]"),
        ([(1, ".. " * 7 + "N")], "row[0]"),
        ([(1, ROW), (1, ".. " * 7 + "N1X")], "row[1]"),
        ([(1, ".. " * 7 + "N1TT")], "row[0]"),
        ([(1, ".. " * 7 + "N1x")], "row[0]"),
        ([(1, ".. " * 7 + "N1fb")], "row[0]"),
        ([(1, ".. " * 7 + "N1Tf")], "row[0]"),
    ],
)
def test_errors_report_their_location(rows: list, location: str) -> None:
    with pytest.raises(TrackFormatError) as error:
        TrackParser().parse(rows)
    assert error.value.location == location
    assert str(error.value).startswith(f"{location}: ")


def test_parses_new_tiles_and_tunnels() -> None:
    track = TrackParser().parse([(1, "J1 I1 O1 <1 >1 N2T N2T N1A")])
    assert [tile.tile_type for tile in track.tiles()][:5] == [
        TileType.JUMP,
        TileType.ICE,
        TileType.AIR,
        TileType.PUSH_LEFT,
        TileType.PUSH_RIGHT,
    ]
    tunnels = [tile.tunnel for tile in track.tiles()]
    assert tunnels == [None] * 5 + [TunnelKind.SQUARE, TunnelKind.SQUARE, TunnelKind.ROUND]


def test_parses_slopes() -> None:
    track = TrackParser().parse([(1, "N1f N1b N2l N2r N1fl N1fr N1bl B3br")])
    slopes = [tile.slope for tile in track.tiles()]
    assert slopes == [
        Slope.FRONT,
        Slope.BACK,
        Slope.LEFT,
        Slope.RIGHT,
        Slope.FRONT_LEFT,
        Slope.FRONT_RIGHT,
        Slope.BACK_LEFT,
        Slope.BACK_RIGHT,
    ]
    last = track.tile_at(7, 0)
    assert last is not None
    assert (last.tile_type, last.level, last.tunnel) == (TileType.BOOST, 3, None)


def test_errors_name_rows_by_the_given_locations() -> None:
    with pytest.raises(TrackFormatError) as error:
        TrackParser().parse([(1, ROW), (1, ".. " * 7 + "X1")], ["track[3]", "track[5]"])
    assert error.value.location == "track[5]"
