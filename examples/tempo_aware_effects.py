#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demonstration of tempo aware effects."""
from klang.audio.effects import Tremolo, Delay, Filter, Transformer
from klang.audio.mixer import StereoMixer
from klang.audio.oscillators import Oscillator, Lfo
from klang.audio.panning import LEFT, RIGHT
from klang.audio.waves import square, triangle, random
from klang.constants import STEREO
from klang.klang import run_klang, Dac
from klang.music.note_values import (
    LARGE_NOTE, WHOLE_NOTE, QUARTER_NOTE, DOTTED_QUARTER_NOTE,
    DOUBLE_DOTTED_QUARTER_NOTE
)


# Params
FEEDBACK = .8
DRY_WET = .4
FILEPATH = 'waterfall.wav'
FILEPATH = None

# Init blocks
osc = Oscillator(wave_func=random)
tremolo = Tremolo(rate=QUARTER_NOTE, intensity=1., wave_func=square)
lfo = Lfo(LARGE_NOTE, wave_func=triangle)
trafo = Transformer.from_limits(lower=110., upper=1100)
fil = Filter()
dac = Dac(nChannels=STEREO)

# Stereo Delay
leftDelay = Delay(time=DOUBLE_DOTTED_QUARTER_NOTE, feedback=FEEDBACK, drywet=DRY_WET)
rightDelay = Delay(time=DOTTED_QUARTER_NOTE, feedback=FEEDBACK, drywet=DRY_WET)
mixer = StereoMixer(nInputs=STEREO, pannings=[LEFT, RIGHT])

# Connect blocks
osc | tremolo | fil.input
lfo | trafo | fil.frequency
fil | leftDelay | mixer.inputs[0]
fil | rightDelay | mixer.inputs[1]
mixer | dac

if __name__ == '__main__':
    run_klang(dac, filepath=FILEPATH)
