# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Pulse Corridor."""

from synthride.core.level import Level
from synthride.core.track_parser import TrackParser

LEVEL = Level(
    name="Pulse Corridor",
    gravity=22.0,
    oxygen_seconds=46.0,
    fuel_capacity=68.0,
    track=TrackParser().parse([
        # first row = start of the track
        (12, ".. .. N1 N1 N1 N1 .. .."),
        # into the corridor
        (12, ".. .. N1T N1T N1T N1T .. .."),
        (6, ".. .. K1T K1T N1T N1T .. .."),
        (8, ".. .. N1T N1T N1T N1T .. .."),
        (6, ".. .. N1T N1T K1T K1T .. .."),
        (8, ".. .. N1T N1T N1T N1T .. .."),
        (6, ".. .. K1T K1T N1T N1T .. .."),
        (4, ".. .. N1 N1 N1 N1 .. .."),
        (4, ".. .. .. .. .. .. .. .."),
        (8, ".. N1 N1 N1 N1 N1 N1 .."),
        # round tunnel slalom
        (5, ".. N1A N1A K1A K1A K1A K1A .."),
        (8, ".. N1A N1A N1A N1A N1A N1A .."),
        (5, ".. K1A K1A K1A K1A N1A N1A .."),
        (8, ".. N1A N1A N1A N1A N1A N1A .."),
        (5, ".. N1A N1A K1A K1A K1A K1A .."),
        (8, ".. N1A N1A N1A N1A N1A N1A .."),
        (5, ".. K1A K1A K1A K1A N1A N1A .."),
        (4, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. R1 R1 R1 R1 R1 R1 .."),
        (2, ".. O1 O1 O1 O1 O1 O1 .."),
        (4, ".. N1 N1 N1 N1 N1 N1 .."),
        # climb out
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. .. N2 N2 N2 N2 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. .. N3 N3 N3 N3 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. .. N4 N4 N4 N4 .. .."),
        # high corridor
        (10, ".. .. N4T N4T N4T N4T .. .."),
        (4, ".. .. S4T S4T S4T S4T .. .."),
        (4, ".. .. B4T B4T B4T B4T .. .."),
        (10, ".. .. N4T N4T N4T N4T .. .."),
        # drop
        (5, ".. .. .. .. .. .. .. .."),
        (1, ".. N2fl N2 N2 N2 N2 N2fr .."),
        (6, ".. N2l N2 N2 N2 N2 N2r .."),
        (1, ".. N2bl N2 N2 N2 N2 N2br .."),
        (6, ".. K2 N2 N2 K2 N2 N2 .."),
        (6, ".. N2 N2 K2 N2 N2 K2 .."),
        (6, ".. N2 K2 N2 N2 K2 N2 .."),
        (2, ".. K2 N2 N2 K2 N2 N2 .."),
        (4, ".. N2 N2 N2 N2 N2 N2 .."),
        (2, ".. R2 R2 R2 R2 R2 R2 .."),
        (2, ".. O2 O2 O2 O2 O2 O2 .."),
        # ice corridor with pusher
        (8, ".. I2T I2T I2T I2T I2T I2T .."),
        (8, ".. I2T >2T >2T >2T I2T I2T .."),
        (8, ".. I2T I2T I2T I2T I2T I2T .."),
        (6, ".. N2 N2 N2 N2 N2 N2 .."),
        # zig in the dark
        # zig on the upper deck
        (1, ".. N2f N2f N2f .. .. .. .."),
        (5, ".. N3 N3 N3 .. .. .. .."),
        (6, ".. .. N3 N3 N3 .. .. .."),
        (6, ".. .. .. N3 N3 N3 .. .."),
        (6, ".. .. .. .. N3 N3 N3 .."),
        (6, ".. .. .. N3 N3 N3 .. .."),
        (6, ".. .. N3 N3 N3 .. .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (1, ".. .. N2 N2 N2 N2 .. .."),
        (1, ".. .. N2f N2f N2f N2f .. .."),
        (1, ".. .. N2b N2b N2b N2b .. .."),
        (1, ".. .. N2f N2f N2f N2f .. .."),
        (1, ".. .. N2b N2b N2b N2b .. .."),
        (1, ".. .. N2f N2f N2f N2f .. .."),
        (1, ".. .. N2b N2b N2b N2b .. .."),
        (1, ".. .. N2 N2 N2 N2 .. .."),
        # deep corridor
        (4, ".. N2 N2 N2 N2 N2 N2 .."),
        (2, ".. R2 R2 R2 R2 R2 R2 .."),
        (2, ".. O2 O2 O2 O2 O2 O2 .."),
        (8, ".. N2A N2A N2A N2A N2A N2A .."),
        (6, ".. K2A K2A K2A K2A N2A N2A .."),
        (7, ".. N2A N2A N2A N2A N2A N2A .."),
        (6, ".. N2A N2A K2A K2A K2A K2A .."),
        (7, ".. N2A N2A N2A N2A N2A N2A .."),
        (6, ".. K2A K2A K2A K2A N2A N2A .."),
        (4, ".. N2A N2A N2A N2A N2A N2A .."),
        (4, ".. N2 N2 N2 N2 N2 N2 .."),
        (4, ".. .. .. .. .. .. .. .."),
        (8, ".. .. N2 N2 N2 N2 .. .."),
        (8, ".. .. N2T N2T N2T N2T .. .."),
        (6, ".. .. N2T N2T K2T K2T .. .."),
        (7, ".. .. N2T N2T N2T N2T .. .."),
        (6, ".. .. K2T K2T N2T N2T .. .."),
        # up to the finish
        (1, ".. .. N2f N2f N2f N2f .. .."),
        (5, ".. .. N3 N3 N3 N3 .. .."),
        # finish line
        (10, ".. .. N3 N3 N3 N3 .. .."),
        (3, ".. .. F3 F3 F3 F3 .. .."),
    ]),
)
