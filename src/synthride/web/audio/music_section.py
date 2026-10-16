# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""One section of the background music: a run of bars sharing chords, grooves, and a melody."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

Chord = tuple[int, int, int]
BassPattern = tuple[int | None, ...]
MelodyBar = tuple[tuple[int, int] | None, ...]


@dataclass(frozen=True)
class MusicSection:
    """A run of bars that cycle through ``chords`` and ``melody``, one entry per bar.

    The bass pattern holds semitone offsets from the bar's chord root, one per sixteenth note, ``None``
    resting. A melody bar holds, for each sixteenth note, the (MIDI note, length in sixteenths) starting
    there, or ``None``.
    """

    NOTE_NAMES: ClassVar[dict[str, int]] = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    HOLD: ClassVar[str] = "-"
    REST: ClassVar[str] = "."

    bars: int
    chords: tuple[Chord, ...]
    bass: BassPattern
    melody: tuple[MelodyBar, ...] = ()
    arpeggio: bool = False
    kick: bool = True
    snare: bool = True
    hats: bool = True
    open_hats: bool = False
    roll: bool = False
    bass_cutoff_hz: float = 900

    @classmethod
    def melody_bar(cls, notation: str) -> MelodyBar:
        """Parse one bar of sixteenth notes such as ``"A4 - C5 . ..."``: names, holds (``-``), and rests (``.``)."""
        tokens = notation.split()
        notes: list[tuple[int, int] | None] = []
        for index, token in enumerate(tokens):
            if token in (cls.HOLD, cls.REST):
                notes.append(None)
                continue
            length = 1
            while index + length < len(tokens) and tokens[index + length] == cls.HOLD:
                length += 1
            notes.append((cls.note(token), length))
        return tuple(notes)

    @classmethod
    def note(cls, name: str) -> int:
        """Return the MIDI note of a name such as ``"G#5"``."""
        sharp = 1 if "#" in name else 0
        return 12 * (int(name[-1]) + 1) + cls.NOTE_NAMES[name[0]] + sharp

    def chord(self, bar: int) -> Chord:
        """Return the chord of bar ``bar`` of this section."""
        return self.chords[bar % len(self.chords)]

    def melody_note(self, bar: int, beat: int) -> tuple[int, int] | None:
        """Return the (MIDI note, length in sixteenths) of the melody starting on ``beat`` of bar ``bar``."""
        if not self.melody:
            return None
        return self.melody[bar % len(self.melody)][beat]
