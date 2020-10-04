"""Micro rhythm demo.

Kick drum and hi-hat sound where the latter is phrased by an LFO.
"""
from klang.audio import Dac, HiHat, Kick, Lfo, triangle
from klang.klang import run_klang
from klang.music import EIGHT_NOTE, SIXTEENTH_NOTE, MicroRhyhtm
from klang.sequencer import Sequencer


# Params
TEMPO = 80
PATTERN = [
    [60, 0, 0, 0, 60, 0, 0, 0, 60, 0, 0, 0, 60, 0, 0, 60],  # Kick drum
    4 * [60, 60, 60, 60],  # Hi-Hat
]
MICRO_RHYTHM_NOTES = [EIGHT_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, EIGHT_NOTE]
RATE = .05


# Setup sequencer / synthesizers
sequencer = Sequencer(PATTERN, tempo=TEMPO)
mixer = (sequencer.outputs[0] | Kick()) + (sequencer.outputs[1] | HiHat())
mixer.gains = [1., .2]

# Apply micro rhythm to Hi-Hat sequence. The phrasing of the micro rhythm is
# controlled by an LFO. apply_micro_rhythm() method has to be called last!
# So that the LFO is included in the internal execOrder of the Sequencer.
lfo = Lfo(frequency=RATE, wave_func=triangle)
mr = MicroRhyhtm(MICRO_RHYTHM_NOTES)
lfo | mr.phrasing
sequencer.apply_micro_rhythm(mr, channel=1)
dac = mixer | Dac()

if __name__ == '__main__':
    run_klang(dac)
