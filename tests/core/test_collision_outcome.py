from synthride.core.collision_outcome import CollisionOutcome


def test_outcomes():
    assert {outcome.name for outcome in CollisionOutcome} == {"LANDED", "NUDGED", "CRASHED", "FELL"}
