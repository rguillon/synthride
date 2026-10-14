# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Neon Highway."""

from synthride.core.level import Level
from synthride.core.track_parser import TrackParser

LEVEL = Level(
    name="Neon Highway",
    gravity=18.0,
    oxygen_seconds=80.0,
    fuel_capacity=100.0,
    track=TrackParser().parse([
        # first row = start of the track
        (12, ".. .. N1 N1 N1 N1 .. .."),
        (10, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. N1 N1 B1 B1 N1 N1 .."),
        (3, ".. N1 N1 N1 N1 N1 N1 .."),
        # a gentle hill
        (1, ".. N1 N1fr N1f N1f N1fl N1 .."),
        (4, ".. N1 N1r N2 N2 N1l N1 .."),
        (1, ".. N1 N1br N1b N1b N1bl N1 .."),
        (5, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. .. .. .. .. .. .. .."),
        (12, ".. N1 N1 N1 N1 N1 N1 .."),
        (12, "N1 N1 N1 N1 .. .. .. .."),
        (6, "N1 N1 N1 N1 N1 N1 N1 N1"),
        (12, ".. .. .. .. N1 N1 N1 N1"),
        (6, ".. .. N1 N1 N1 N1 N1 N1"),
        # ramp up to the second deck
        (1, ".. .. N1f N1f N1f N1f .. .."),
        (11, ".. .. N2 N2 N2 N2 .. .."),
        (2, ".. .. N2 R2 R2 N2 .. .."),
        (8, ".. .. N2 N2 N2 N2 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (10, ".. .. N2 N2 N2 N2 .. .."),
        (10, ".. N1 N1 N1 N1 N1 N1 .."),
        (12, ".. K1 N1 N1 N1 N1 K1 .."),
        (2, ".. N1 B1 N1 N1 B1 N1 .."),
        (2, ".. N1 N1 N1 N1 N1 N1 .."),
        # ramp up, then kick over the gap
        (1, ".. N1f N1f N1f N1f N1f N1f .."),
        (10, ".. N2 N2 N2 N2 N2 N2 .."),
        (1, ".. N2f N2f N2f N2f N2f N2f .."),
        (4, ".. .. .. .. .. .. .. .."),
        (14, ".. N1 N1 N1 N1 N1 N1 .."),
        (3, ".. N1 N1 S1 S1 N1 N1 .."),
        # second lap: lane changes
        (10, ".. N1 N1 N1 N1 N1 N1 .."),
        (12, ".. .. .. N1 N1 N1 N1 N1"),
        (12, ".. .. .. .. N1 N1 N1 .."),
        (10, ".. .. .. N1 N1 N1 N1 .."),
        (12, ".. N1 N1 N1 N1 N1 .. .."),
        (12, ".. N1 N1 N1 .. .. .. .."),
        (6, "N1 N1 N1 N1 N1 N1 .. .."),
        (8, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. R1 R1 R1 R1 R1 R1 .."),
        # banked edges
        (1, ".. N1fl N1 N1 N1 N1 N1fr .."),
        (8, ".. N1l N1 N1 N1 N1 N1r .."),
        (1, ".. N1bl N1 N1 N1 N1 N1br .."),
        # boost into a long jump
        (2, ".. N1 B1 B1 B1 B1 N1 .."),
        (10, ".. N1 N1 N1 N1 N1 N1 .."),
        (5, ".. .. .. .. .. .. .. .."),
        (14, ".. N1 N1 N1 N1 N1 N1 .."),
        # hop up the step and across
        (12, ".. .. N2 N2 N2 N2 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (12, ".. .. N2 N2 N2 N2 .. .."),
        (10, ".. N1 N1 N1 N1 N1 N1 .."),
        # burning lanes
        (10, ".. K1 N1 N1 N1 N1 K1 .."),
        (10, ".. K1 K1 N1 N1 K1 K1 .."),
        (10, ".. K1 N1 N1 N1 N1 K1 .."),
        (10, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. N1 N1 B1 B1 N1 N1 .."),
        (12, ".. N1 N1 N1 N1 N1 N1 .."),
        (4, ".. .. .. .. .. .. .. .."),
        (12, ".. N1 N1 N1 N1 N1 N1 .."),
        (3, ".. N1 N1 S1 S1 N1 N1 .."),
        (10, ".. .. N1 N1 N1 N1 .. .."),
        (3, ".. .. F1 F1 F1 F1 .. .."),
    ]),
)
