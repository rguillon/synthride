import pytest

from synthride.core.level_parser import LevelFormatError, LevelParser
from synthride.core.tile_type import TileType

VALID = """\
name: Neon Test   # comment
gravity: 20
oxygen: 30
fuel: 50
---
.. .. N1 N1 N1 N1 .. ..
# a comment line

B2 S3 K4 R1 F1 N1 .. ..
"""


def test_parses_header_and_rows():
    level = LevelParser().parse(VALID)
    assert level.name == "Neon Test"
    assert (level.gravity, level.oxygen_seconds, level.fuel_capacity) == (20, 30, 50)
    assert level.track.row_count == 2
    assert level.track.tile_at(0, 0) is None
    boost = level.track.tile_at(0, 1)
    assert boost is not None
    assert (boost.tile_type, boost.level, boost.row, boost.column) == (TileType.BOOST, 2, 1, 0)
    kill = level.track.tile_at(2, 1)
    assert kill is not None
    assert kill.tile_type is TileType.KILL


def test_defaults_when_header_is_empty():
    level = LevelParser().parse("---\n" + ".. " * 8)
    assert level.name == "Untitled"


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ("name: x\n" + ".. " * 8, 2),
        ("bogus\n---\n" + ".. " * 8, 1),
        ("speed: 3\n---\n" + ".. " * 8, 1),
        ("gravity: high\n---\n" + ".. " * 8, 1),
        ("---\n.. ..", 2),
        ("---\n" + ".. " * 7 + "X1", 2),
        ("---\n" + ".. " * 7 + "N9", 2),
        ("---\n" + ".. " * 7 + "N", 2),
        ("---\n", 1),
    ],
)
def test_errors_report_line_number(text, line):
    with pytest.raises(LevelFormatError) as error:
        LevelParser().parse(text)
    assert error.value.line_number == line
    assert f"line {line}" in str(error.value)
