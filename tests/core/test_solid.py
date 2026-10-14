from synthride.core.solid import Solid
from synthride.core.tile import Tile
from synthride.core.tile_type import TileType


def test_tile_block_and_bare_shell():
    tile = Tile(TileType.NORMAL, 1, 2, 1)
    assert Solid(tile.bounding_box, tile).tile is tile
    assert Solid(tile.bounding_box).tile is None
