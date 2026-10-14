# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.web.synth_music import SynthMusic
from synthride.web.synth_voices import SynthVoices
from tests.web.fakes.fake_audio_context import FakeAudioContext
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def make_music() -> tuple[FakeAudioContext, SynthVoices, SynthMusic]:
    context = FakeAudioContext()
    voices = SynthVoices(FakeJsBridge(), context, FakeJsObject("destination"))
    return context, voices, SynthMusic(voices)


def test_silent_until_started() -> None:
    context, _, music = make_music()
    music.update()
    assert context.oscillators == []


def test_start_resumes_audio_and_schedules_ahead() -> None:
    context, _, music = make_music()
    music.start()
    music.update()
    assert context.resume.calls == [()]
    steps = int((SynthMusic.LOOKAHEAD - 0.1) / music.step_seconds) + 1
    assert len(context.oscillators) >= steps
    assert all(osc.start.calls[0][0] < SynthMusic.LOOKAHEAD for osc in context.oscillators)


def test_downbeat_has_bass_kick_and_detuned_pad() -> None:
    context, _, music = make_music()
    music.schedule_step(0, 1.0)
    assert len(context.oscillators) == 1 + 1 + 3 * 2


def test_skips_ahead_after_a_stall() -> None:
    context, _, music = make_music()
    music.start()
    context.currentTime = 100.0
    music.update()
    assert min(osc.start.calls[0][0] for osc in context.oscillators) >= 100


def test_toggle_mute() -> None:
    _, voices, music = make_music()
    assert voices.output.gain.value == SynthMusic.VOLUME
    music.toggle_mute()
    assert voices.output.gain.value == 0
    music.toggle_mute()
    assert voices.output.gain.value == SynthMusic.VOLUME


def test_starting_again_keeps_the_beat_going() -> None:
    context, _, music = make_music()
    music.start()
    music.update()
    scheduled = len(context.oscillators)
    music.start()
    music.update()
    assert len(context.oscillators) == scheduled
    assert context.resume.calls == [(), ()]


def bar_of(name_index: int) -> int:
    return sum(section.bars for section in SynthMusic.SONG[:name_index])


VERSE, CHORUS, BREAKDOWN, BUILD = 1, 2, 3, 4


def test_song_is_long_before_it_loops() -> None:
    assert SynthMusic.song_bars() * SynthMusic.STEPS_PER_BAR * 60 / SynthMusic.BPM / 4 > 90
    assert SynthMusic.section_at(SynthMusic.song_bars()) == (SynthMusic.SONG[0], 0)
    last = SynthMusic.SONG[-1]
    assert SynthMusic.section_at(SynthMusic.song_bars() - 1) == (last, last.bars - 1)


def test_backbeat_has_a_snare() -> None:
    context, _, music = make_music()
    music.schedule_step(bar_of(VERSE) * SynthMusic.STEPS_PER_BAR + 4, 1.0)
    assert len(context.noise_sources) == 1


def test_intro_has_no_snare() -> None:
    context, _, music = make_music()
    music.schedule_step(4, 1.0)
    assert context.noise_sources == []


def test_section_ends_with_a_snare_fill() -> None:
    context, _, music = make_music()
    last_bar = bar_of(VERSE) + SynthMusic.SONG[VERSE].bars - 1
    music.schedule_step(last_bar * SynthMusic.STEPS_PER_BAR + 14, 1.0)
    assert len(context.noise_sources) == 1


def test_build_up_rolls_faster() -> None:
    context, _, music = make_music()
    first, last = bar_of(BUILD), bar_of(BUILD) + SynthMusic.SONG[BUILD].bars - 1
    for step in range(SynthMusic.STEPS_PER_BAR):
        music.schedule_step(first * SynthMusic.STEPS_PER_BAR + step, 1.0)
    early = len(context.noise_sources)
    for step in range(SynthMusic.STEPS_PER_BAR):
        music.schedule_step(last * SynthMusic.STEPS_PER_BAR + step, 1.0)
    assert len(context.noise_sources) - early == 4 * early


def test_breakdown_drops_the_kick() -> None:
    context, _, music = make_music()
    music.schedule_step(bar_of(BREAKDOWN) * SynthMusic.STEPS_PER_BAR, 1.0)
    assert all(osc.type != "sine" for osc in context.oscillators)


def test_lead_arpeggio_plays_in_the_second_half_of_the_phrase() -> None:
    context, _, music = make_music()
    first = bar_of(VERSE) * SynthMusic.STEPS_PER_BAR
    music.schedule_step(first + 1, 1.0)
    without_lead = len(context.oscillators)
    music.schedule_step(first + 2 * SynthMusic.STEPS_PER_BAR + 2, 1.0)
    assert len(context.oscillators) == 2 * without_lead + 1


def test_chorus_plays_a_melody() -> None:
    context, _, music = make_music()
    music.schedule_step(bar_of(CHORUS) * SynthMusic.STEPS_PER_BAR + 2, 1.0)
    assert sum(osc.type == "square" for osc in context.oscillators) == 1
