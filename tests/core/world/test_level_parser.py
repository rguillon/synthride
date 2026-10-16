# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.world.level_parser import LevelFormatError, LevelParser
from synthride.core.world.slope import Slope
from synthride.core.world.tile_type import TileType
from synthride.core.world.tunnel_kind import TunnelKind
from tests.level_json import level_json

VALID = """\
{
  "name": "Neon Test",
  "gravity": 20,
  "oxygen": 30,
  "fuel": 50.5,
  "track": [
    "# first row = start",
    [3, ".. .. N1 N1 N1 N1 .. .."],
    "",
    "B2 S3 K4 R1 F1 N1 .. ..  # trailing comment",
    [2, "N1 N1f N2 N2A N2A N2 N2 N2  # a ramp and a tunnel"]
  ]
}
"""

ROW = ".. " * 8


def test_parses_settings_and_rows() -> None:
    level = LevelParser().parse(VALID)
    assert level.name == "Neon Test"
    assert (level.gravity, level.oxygen_seconds, level.fuel_capacity) == (20, 30, 50.5)
    assert level.track.row_count == 6
    assert [level.track.tile_at(2, row) is not None for row in range(6)] == [True] * 6
    assert level.track.tile_at(0, 0) is None
    boost = level.track.tile_at(0, 3)
    assert boost is not None
    assert (boost.tile_type, boost.level, boost.row, boost.column) == (TileType.BOOST, 2, 3, 0)
    ramp, tunnel = level.track.tile_at(1, 5), level.track.tile_at(3, 4)
    assert ramp is not None
    assert ramp.slope is Slope.FRONT
    assert tunnel is not None
    assert tunnel.tunnel is TunnelKind.ROUND


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
        (level_json("# start", 8), "track[1]"),
        (level_json([1, ROW, 2]), "track[0]"),
        (level_json(ROW, [0, ROW]), "track[1]"),
        (level_json([2, 7]), "track[0]"),
        (level_json(".. .."), "track[0]"),
        (level_json("# start", ROW, ".. " * 7 + "X1"), "track[2]"),
        (level_json([3, ROW], [1, ".. " * 7 + "N9"]), "track[1]"),
        (level_json(".. " * 7 + "N1fb"), "track[0]"),
    ],
)
def test_errors_report_their_location(text: str, location: str) -> None:
    with pytest.raises(LevelFormatError) as error:
        LevelParser().parse(text)
    assert error.value.location == location
    assert str(error.value).startswith(f"{location}: ")
    assert f"{location}: {location}" not in str(error.value)
