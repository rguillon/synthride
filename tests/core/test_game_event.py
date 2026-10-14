from synthride.core.game_event import GameEvent


def test_contains_death_causes():
    assert {"CRASHED", "FELL", "BURNED", "OUT_OF_FUEL", "OUT_OF_OXYGEN"} <= {event.name for event in GameEvent}
