# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.level_parser import LevelFormatError, LevelParser
from synthride.core.tile_type import TileType
from synthride.core.tunnel_kind import TunnelKind
from tests.level_json import level_json

VALID = """\
{
  "name": "Neon Test",
  "gravity": 20,
  "oxygen": 30,
  "fuel": 50.5,
  "track": [
    "# first row = start",
    ".. .. N1 N1 N1 N1 .. ..",
    "",
    "B2 S3 K4 R1 F1 N1 .. ..  # trailing comment"
  ]
}
"""

ROW = ".. " * 8


def test_parses_settings_and_rows() -> None:
    level = LevelParser().parse(VALID)
    assert level.name == "Neon Test"
    assert (level.gravity, level.oxygen_seconds, level.fuel_capacity) == (20, 30, 50.5)
    assert level.track.row_count == 2
    assert level.track.tile_at(0, 0) is None
    boost = level.track.tile_at(0, 1)
    assert boost is not None
    assert (boost.tile_type, boost.level, boost.row, boost.column) == (TileType.BOOST, 2, 1, 0)
    kill = level.track.tile_at(2, 1)
    assert kill is not None
    assert kill.tile_type is TileType.KILL


def test_defaults_when_only_the_track_is_given() -> None:
    level = LevelParser().parse(level_json(ROW))
    assert level.name == "Untitled"


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ('{\n  "name": "x"\n  "fuel": 1\n}', "line 3"),
        ("[]", "level"),
        ('{"name": "x"}', "level"),
        (level_json(ROW, speed=3), "speed"),
        (level_json(ROW, gravity="high"), "gravity"),
        (level_json(ROW, fuel=True), "fuel"),
        (level_json(ROW, name=7), "name"),
        ('{"track": ".. .. .. .. .. .. .. .."}', "track"),
        (level_json("# nothing"), "track"),
        ('{"track": ["# start", 8]}', "track[1]"),
        (level_json(".. .."), "track[0]"),
        (level_json("# start", ROW, ".. " * 7 + "X1"), "track[2]"),
        (level_json(".. " * 7 + "N9"), "track[0]"),
        (level_json(".. " * 7 + "N"), "track[0]"),
        (level_json(ROW, ".. " * 7 + "N1X"), "track[1]"),
        (level_json(".. " * 7 + "N1TT"), "track[0]"),
    ],
)
def test_errors_report_their_location(text: str, location: str) -> None:
    with pytest.raises(LevelFormatError) as error:
        LevelParser().parse(text)
    assert error.value.location == location
    assert str(error.value).startswith(f"{location}: ")


def test_parses_new_tiles_and_tunnels() -> None:
    track = LevelParser().parse(level_json("J1 I1 O1 <1 >1 N2T N2T N1A")).track
    assert [tile.tile_type for tile in track.tiles()][:5] == [
        TileType.JUMP,
        TileType.ICE,
        TileType.AIR,
        TileType.PUSH_LEFT,
        TileType.PUSH_RIGHT,
    ]
    tunnels = [tile.tunnel for tile in track.tiles()]
    assert tunnels == [None] * 5 + [TunnelKind.SQUARE, TunnelKind.SQUARE, TunnelKind.ROUND]
