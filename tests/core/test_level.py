from synthride.core.level import Level
from synthride.core.track import Track


def test_defaults():
    level = Level("Test", Track([[None] * 8]))
    assert level.gravity > 0
    assert level.oxygen_seconds > 0
    assert level.fuel_capacity > 0
