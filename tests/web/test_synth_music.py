from synthride.web.synth_music import SynthMusic
from synthride.web.synth_voices import SynthVoices
from tests.web.fakes.fake_audio_context import FakeAudioContext
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def make_music():
    context = FakeAudioContext()
    voices = SynthVoices(FakeJsBridge(), context, FakeJsObject("destination"))
    return context, voices, SynthMusic(voices)


def test_silent_until_started():
    context, _, music = make_music()
    music.update()
    assert context.oscillators == []


def test_start_resumes_audio_and_schedules_ahead():
    context, _, music = make_music()
    music.start()
    music.update()
    assert context.resume.calls == [()]
    steps = int((SynthMusic.LOOKAHEAD - 0.1) / music.step_seconds) + 1
    assert len(context.oscillators) >= steps
    assert all(osc.start.calls[0][0] < SynthMusic.LOOKAHEAD for osc in context.oscillators)


def test_downbeat_has_bass_kick_and_detuned_pad():
    context, _, music = make_music()
    music.schedule_step(0, 1.0)
    assert len(context.oscillators) == 1 + 1 + 3 * 2


def test_skips_ahead_after_a_stall():
    context, _, music = make_music()
    music.start()
    context.currentTime = 100.0
    music.update()
    assert min(osc.start.calls[0][0] for osc in context.oscillators) >= 100


def test_toggle_mute():
    _, voices, music = make_music()
    assert voices.output.gain.value == SynthMusic.VOLUME
    music.toggle_mute()
    assert voices.output.gain.value == 0
    music.toggle_mute()
    assert voices.output.gain.value == SynthMusic.VOLUME
