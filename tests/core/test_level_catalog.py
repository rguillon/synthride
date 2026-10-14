from synthride.core.level_catalog import LevelCatalog


def test_lists_bundled_levels_in_order():
    names = LevelCatalog().file_names()
    assert len(names) >= 3
    assert names == sorted(names)


def test_all_bundled_levels_parse_and_are_finishable_in_principle():
    for level in LevelCatalog().load_all():
        assert level.name
        assert level.track.row_count > 50
        first_row = [level.track.tile_at(column, 0) for column in range(8)]
        assert any(first_row), f"{level.name} has no tile to start on"
