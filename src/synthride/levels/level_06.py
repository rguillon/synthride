# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Sky Ladder."""

from synthride.core.level import Level
from synthride.core.track_parser import TrackParser

LEVEL = Level(
    name="Sky Ladder",
    gravity=16.0,
    oxygen_seconds=70.0,
    fuel_capacity=80.0,
    track=TrackParser().parse([
        # first row = start of the track
        (12, ".. .. N1 N1 N1 N1 .. .."),
        # first rungs: one jump per step
        (10, ".. .. N2 N2 N2 N2 .. .."),
        (10, ".. .. N3 N3 N3 N3 .. .."),
        (10, ".. .. N4 N4 N4 N4 .. .."),
        (4, ".. .. .. .. .. .. .. .."),
        (12, ".. N2 N2 N2 N2 N2 N2 .."),
        # jump pad straight to the top
        (2, ".. .. J2 J2 J2 J2 .. .."),
        (4, ".. .. .. .. .. .. .. .."),
        (2, ".. .. N4 N4 N4 N4 .. .."),
        # over the summit
        (1, ".. .. N4f N4f N4f N4f .. .."),
        (1, ".. .. N5f N5f N5f N5f .. .."),
        (12, ".. .. N6 N6 N6 N6 .. .."),
        (1, ".. .. N5b N5b N5b N5b .. .."),
        (1, ".. .. N4b N4b N4b N4b .. .."),
        (2, ".. .. R4 R4 R4 R4 .. .."),
        (6, ".. .. N4 N4 N4 N4 .. .."),
        # stairs down over the void
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. .. N3 N3 N3 N3 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. .. N2 N2 N2 N2 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (12, ".. N1 N1 N1 N1 N1 N1 .."),
        # quick steps up
        # quick ramps up
        (1, ".. .. N1f N1f N1f N1f .. .."),
        (5, ".. .. N2 N2 N2 N2 .. .."),
        (1, ".. .. N2f N2f N2f N2f .. .."),
        (7, ".. .. N3 N3 N3 N3 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (10, ".. .. N3 N3 N3 N3 .. .."),
        (2, ".. .. B3 B3 B3 B3 .. .."),
        (8, ".. .. N3 N3 N3 N3 .. .."),
        (6, ".. .. .. .. .. .. .. .."),
        (12, ".. N2 N2 N2 N2 N2 N2 .."),
        # pillars: high blocks to steer around
        (6, ".. N2 N4 N2 N2 N2 N2 .."),
        (6, ".. N2 N2 N2 N2 N4 N2 .."),
        (6, ".. N2 N2 N4 N4 N2 N2 .."),
        (6, ".. N2 N2 N2 N2 N2 N2 .."),
        (6, ".. N4 N2 N2 N2 N2 N4 .."),
        (8, ".. N2 N2 N2 N2 N2 N2 .."),
        (2, ".. N2 O2 O2 O2 O2 N2 .."),
        (8, ".. N2 N2 N2 N2 N2 N2 .."),
        # jump pad over the long drop
        (2, ".. .. J2 J2 J2 J2 .. .."),
        (8, ".. .. .. .. .. .. .. .."),
        (16, ".. .. N2 N2 N2 N2 .. .."),
        # narrow staircase
        (1, ".. .. .. N2f N2f .. .. .."),
        (7, ".. .. .. N3 N3 .. .. .."),
        (1, ".. .. .. N3f N3f .. .. .."),
        (7, ".. .. .. N4 N4 .. .. .."),
        (2, ".. .. .. R4 R4 .. .. .."),
        (8, ".. .. .. N4 N4 .. .. .."),
        (4, ".. .. .. .. .. .. .. .."),
        (8, ".. .. N3 N3 N3 N3 .. .."),
        (4, ".. .. .. .. .. .. .. .."),
        (10, ".. .. N2 N2 N2 N2 .. .."),
        # the ladder: short rungs, keep the rhythm
        (8, ".. .. N1 N1 N1 N1 .. .."),
        (10, ".. .. N2 N2 N2 N2 .. .."),
        (2, ".. .. .. .. .. .. .. .."),
        (10, ".. .. N3 N3 N3 N3 .. .."),
        (2, ".. .. .. .. .. .. .. .."),
        (10, ".. .. N4 N4 N4 N4 .. .."),
        (2, ".. .. B4 B4 B4 B4 .. .."),
        (6, ".. .. N4 N4 N4 N4 .. .."),
        # the long fall home
        (6, ".. .. .. .. .. .. .. .."),
        (14, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. .. J1 J1 J1 J1 .. .."),
        (4, ".. .. .. .. .. .. .. .."),
        (14, ".. .. N3 N3 N3 N3 .. .."),
        (3, ".. .. F3 F3 F3 F3 .. .."),
    ]),
)
