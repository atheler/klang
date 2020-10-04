"""Sequencer drum kit demo with synthesizer pad sound."""
from klang.audio import (
    AR, Dac, Delay, HiHat, Kick, Oscillator, PolyphonicSynthesizer, Voice
)
from klang.sequencer import Sequencer
from klang.klang import run_klang


# Params
TEMPO = 120
PATTERN = [
    [60, 0, 0, 60, 0, 0, 60, 0, 60, 0, 0, 60, 0, 60, 0, 60],  # Kick drum
    4 * [0, 0, 127, 0],  # Hi-Hat
    [65, 70, 65, 68, 72, 65, 70, 65, 68, 72, 65, 70, 65, 68, 72, 65],  # Synthesizer
]


seq = Sequencer(
    PATTERN,
    tempo=TEMPO,
    relNoteLength=.8
)

# Create synthesizer
osc = Oscillator()
env = AR(attack=.1, release=.02)
voice = Voice(envelope=env, oscillator=osc)
synthesizer = PolyphonicSynthesizer(voice)

# Setup audio path
mixer = (seq.outputs[0] | Kick(decay=.8))\
        + (seq.outputs[1] | HiHat())\
        + (seq.outputs[2] | synthesizer | Delay(time=.25, feedback=.25))
mixer.gains = [.7, .1, 1.]
dac = mixer | Dac()

if __name__ == '__main__':
    run_klang(dac)
