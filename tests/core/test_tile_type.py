from synthride.core.tile_type import TileType


def test_letters_are_unique_and_single_characters():
    letters = [tile_type.value for tile_type in TileType]
    assert len(set(letters)) == len(letters)
    assert all(len(letter) == 1 for letter in letters)


def test_lookup_by_letter():
    assert TileType("B") is TileType.BOOST
