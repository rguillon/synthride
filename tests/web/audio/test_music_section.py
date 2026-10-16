# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.web.audio.music_section import MusicSection


def test_note_names_map_to_midi() -> None:
    assert MusicSection.note("A4") == 69
    assert MusicSection.note("C5") == 72
    assert MusicSection.note("G#5") == 80


def test_melody_bar_counts_holds_into_note_lengths() -> None:
    assert MusicSection.melody_bar("A4 - - . C5 -") == ((69, 3), None, None, None, (72, 2), None)


def test_chords_and_melody_cycle_over_the_bars() -> None:
    melody = (MusicSection.melody_bar("A4"), MusicSection.melody_bar("C5"))
    section = MusicSection(4, ((57, 60, 64), (53, 57, 60)), (0,), melody)
    assert section.chord(2) == (57, 60, 64)
    assert section.melody_note(3, 0) == (72, 1)
    assert MusicSection(4, ((57, 60, 64),), (0,)).melody_note(0, 0) is None
