# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.gameplay.game_event import GameEvent
from synthride.web.audio.sound_effects import SoundEffects
from synthride.web.audio.synth_voices import SynthVoices
from tests.web.fakes.fake_audio_context import FakeAudioContext
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def make_effects() -> tuple[FakeAudioContext, SoundEffects]:
    context = FakeAudioContext()
    return context, SoundEffects(SynthVoices(FakeJsBridge(), context, FakeJsObject("destination")))


def test_every_audible_event_makes_a_sound() -> None:
    for event in GameEvent:
        context, effects = make_effects()
        effects.play([event])
        silent = {GameEvent.LEVEL_STARTED, GameEvent.LIFE_LOST, GameEvent.SCRAPED_LEFT, GameEvent.SCRAPED_RIGHT}
        assert bool(context.oscillators or context.noise_sources) == (event not in silent), event


def test_duplicate_events_play_once() -> None:
    context, effects = make_effects()
    effects.play([GameEvent.JUMPED, GameEvent.JUMPED])
    assert len(context.oscillators) == 1
