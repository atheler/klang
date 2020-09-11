"""Reverb demo."""
from klang.audio import AR, MonophonicSynthesizer, Oscillator, Reverb, Voice
from klang.klang import Dac, run_klang
from klang.sequencer import Sequencer


def create_synthesizer(attack=.01, release=1.):
    """Create a monophonic synthesizer instance."""
    osc = Oscillator()
    env = AR(attack, release)
    voice = Voice(osc, env)
    return MonophonicSynthesizer(voice)


# Init the 3x synthesizer voices: base, upper and lower
base = Sequencer([[
    60, 0, 0, 0, 62, 0, 0, 0, 67, 0, 0, 0, 69, 0, 0, 0,
    60, 0, 0, 0, 62, 0, 0, 0, 67, 0, 0, 0, 69, 0, 0, 0,
    60, 0, 0, 0, 62, 0, 0, 0, 67, 0, 0, 0, 71, 0, 0, 0,
]], tempo=40) | create_synthesizer()
upper = Sequencer([[
    0, 0, 0, 0, 0, 0, 76, 0, 0, 72, 0, 0, 0, 0, 0, 0,
]], tempo=120) | create_synthesizer()
lower = Sequencer([[
    53, 0, 60, 0,
    55, 0, 60, 0,
    57, 0, 60, 0,
    62, 0, 60, 0,
]], tempo=80) | create_synthesizer()

mixer = (base + upper + lower)
run_klang(mixer | Reverb(decay=3., dryWet=.7) | Dac(nChannels=1))
