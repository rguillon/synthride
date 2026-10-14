from dataclasses import dataclass


@dataclass(frozen=True)
class GameConfig:
    """Every gameplay tunable in one place."""

    fixed_step: float = 1 / 120

    ship_width: float = 0.7
    ship_height: float = 0.3
    ship_length: float = 0.8

    max_speed: float = 14.0
    acceleration: float = 7.0
    brake_deceleration: float = 14.0
    boost_factor: float = 1.35
    boost_decay: float = 2.5
    slow_factor: float = 0.45

    min_strafe_speed: float = 2.5
    strafe_ratio: float = 0.3
    jump_velocity: float = 6.5

    step_tolerance: float = 0.12
    crash_overlap_ratio: float = 0.35
    fall_limit_y: float = -4.0

    fuel_per_unit: float = 0.25
    lives: int = 3
    dying_seconds: float = 1.6
    level_won_seconds: float = 2.5
