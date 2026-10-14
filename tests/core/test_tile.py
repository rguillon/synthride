from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3


def test_top_depends_on_level():
    assert Tile(TileType.NORMAL, 0, 0, 3).top == 1.5


def test_bounding_box_spans_its_cell_from_the_abyss():
    box = Tile(TileType.NORMAL, column=2, row=5, level=2).bounding_box
    assert box.minimum == Vector3(2, Tile.BOTTOM, 5)
    assert box.maximum == Vector3(3, 1.0, 6)
