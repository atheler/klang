#!/usr/bin/env python3
"""Micro rhythm demo."""
from klang.audio.klanggeber import KlangGeber
from klang.audio.mixer import Mixer
from klang.audio.oscillators import Lfo
from klang.audio.sequencer import Sequencer
from klang.audio.synthesizer import Kick, HiHat
from klang.audio.waves import triangle
from klang.music.note_values import QUARTER_NOTE, EIGHT_NOTE, SIXTEENTH_NOTE
from klang.music.rhythm import MicroRhyhtm


# Params
TEMPO = 80
PATTERN = [
    [60, 0, 0, 0, 60, 0, 0, 0, 60, 0, 0, 0, 60, 0, 0, 60],  # Kick drum
    4 * [60, 60, 60, 60],  # Hi-Hat
]
#FILENAME = 'micro_rhythm.wav'
FILENAME = None
SOME_MICRO_RHYHTMS = [
    MicroRhyhtm([QUARTER_NOTE, EIGHT_NOTE], name='Swing'),
    MicroRhyhtm([EIGHT_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE], name='Afro-Cuban Triplet'),
    MicroRhyhtm([EIGHT_NOTE, SIXTEENTH_NOTE, EIGHT_NOTE], name='Gnawa Triplet'),
    MicroRhyhtm([EIGHT_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, EIGHT_NOTE], name='Gnawa'),
    MicroRhyhtm([EIGHT_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, EIGHT_NOTE, SIXTEENTH_NOTE], name='Mad Professor Braff'),
        
]


seq = Sequencer(
    PATTERN,
    tempo=TEMPO,
    relNoteDuration=.01
)


# Attach micro rhythm to sequences[1]
#mr = MicroRhyhtm([QUARTER_NOTE, EIGHT_NOTE], phrasing=1.)
mr = MicroRhyhtm([EIGHT_NOTE, SIXTEENTH_NOTE, SIXTEENTH_NOTE, EIGHT_NOTE], phrasing=1.)
seq.sequences[1].connect_micro_rhythm(mr)

# Setup synthesizers
hihat = HiHat()
kick = Kick()
mixer = Mixer(2, gains=[1, .2])
lfo = Lfo(frequency=.05, shape=1, wave_func=triangle)
lfo.output.connect(mr.phrasing)  # Lfo controls phrasing factor


with KlangGeber(nOutputs=1, filepath=FILENAME) as dac:
    seq.outputs[0].connect(kick.input)
    seq.outputs[1].connect(hihat.input)
    kick.output.connect(mixer.inputs[0])
    hihat.output.connect(mixer.inputs[1])
    mixer.output.connect(dac.input)
