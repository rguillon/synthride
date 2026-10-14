# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.web.synth_voices import SynthVoices
from tests.web.fakes.fake_audio_context import FakeAudioContext
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def make_voices() -> tuple[FakeAudioContext, FakeJsObject, SynthVoices]:
    context = FakeAudioContext()
    destination = FakeJsObject("destination")
    return context, destination, SynthVoices(FakeJsBridge(), context, destination)


def test_routes_output_to_destination_and_prepares_noise() -> None:
    context, destination, voices = make_voices()
    assert voices.output.connect.calls == [(destination,)]
    assert context.createBuffer.calls == [(1, 50, 100)]


def test_frequency_of_a4_and_a5() -> None:
    assert SynthVoices.frequency(69) == 440
    assert SynthVoices.frequency(81) == pytest.approx(880)


def test_tone_starts_and_stops_an_oscillator() -> None:
    context, _, voices = make_voices()
    context.currentTime = 2.0
    voices.tone("square", 220, voices.now, 0.5, 0.3, end_hz=440, cutoff_hz=1000)
    (oscillator,) = context.oscillators
    assert oscillator.type == "square"
    assert oscillator.start.calls == [(2.0,)]
    assert oscillator.stop.calls == [(2.55,)]
    assert oscillator.frequency.exponentialRampToValueAtTime.calls == [(440, 2.5)]


def test_noise_plays_the_shared_buffer() -> None:
    context, _, voices = make_voices()
    voices.noise(1.0, 0.1, 0.5, highpass_hz=3000)
    voices.noise(1.0, 2.0, 0.5)
    first, second = context.noise_sources
    assert first.start.calls == [(1.0, 0, pytest.approx(0.15))]
    assert second.start.calls == [(1.0, 0, SynthVoices.NOISE_SECONDS)]
