#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arpeggiator demonstration."""
from klang.arpeggiator import Arpeggiator
from klang.audio.effects import Delay, Filter, Transformer
from klang.audio.envelope import ADSR
from klang.klang import Klang
from klang.audio.oscillators import Lfo
from klang.audio.oscillators import Oscillator
from klang.audio.synthesizer import MonophonicSynthesizer
from klang.audio.voices import OscillatorVoice
from klang.audio.waves import sawtooth, triangle, sine
from klang.messages import Note
from klang.audio.sequencer import Sequencer
from klang.audio.mixer import Mixer


Alow = Note(pitch=57)
C = Note(pitch=60)
D = Note(pitch=62)
E = Note(pitch=64)
F = Note(pitch=65)
G = Note(pitch=67)
A = Note(pitch=69)


def build_synthesizer(attack=.1, decay=.2, sustain=.3, release=.4, wave_func=sine):
    env = ADSR(attack, decay, sustain, release)
    osc = Oscillator(wave_func=wave_func)
    voice = OscillatorVoice(env, osc)
    return MonophonicSynthesizer(voice)


if __name__ == '__main__':
    # Arp synthesizer
    synthesizer = build_synthesizer(wave_func=sawtooth)

    arp = Arpeggiator(frequency=.2, nSteps=16, order='alternating')
    #arp.arpeggio.process_notes(C, D, F, G, A)
    #arp.arpeggio.process_notes(C, D, Alow, G, A, F)
    arp.arpeggio.process_notes(Alow, C, E, F, G, A)
    #arp.arpeggio.process_notes( Note(pitch=57), C, D, E, G, F,)
    delay = Delay(time=0.76, feedback=.9)
    lfo = Lfo(frequency=.1, wave_func=triangle)
    trafo = Transformer.from_limits(100., 3000.)
    fil = Filter(frequency=220.)

    # Bass
    sequencer = Sequencer(
        pattern=[[38, 41, 0, 0, 36, 34, 0, 0]],
        tempo=15,
        relNoteDuration=1.
    )
    bass = build_synthesizer(wave_func=sine, attack=4., sustain=1., release=4.)


    klang = Klang(nOutputs=1)

    # Old style
    """
    mixer = Mixer(gains=[1., .3])
    arp.output.connect(synthesizer.input)
    synthesizer.output.connect(fil.input)
    lfo.output.connect(trafo.input)
    trafo.output.connect(fil.frequency)
    fil.output.connect(delay.input)
    delay.output.connect(mixer.inputs[0])

    # Bass
    sequencer.outputs[0].connect(bass.input)
    bass.output.connect(mixer.inputs[1])

    mixer.output.connect(klang.dac.input)
    """

    # New style
    lfo | trafo | fil.frequency
    mixer = (arp | synthesizer | fil | delay) + (sequencer | bass)
    mixer.gains = [1., .3]
    mixer | klang.dac

    klang.start()
