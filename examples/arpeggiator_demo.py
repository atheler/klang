"""Arpeggiator demonstration."""
from klang.arpeggiator import Arpeggiator
from klang.audio import (
    ADSR, Dac, Delay, Filter, Lfo, MonophonicSynthesizer, Oscillator, Voice,
    sawtooth, sine, triangle,
)
from klang.klang import run_klang
from klang.messages import Note
from klang.sequencer import Sequencer
from klang.music.note_values import WHOLE_NOTE


Alow = Note(pitch=57)
C = Note(pitch=60)
D = Note(pitch=62)
E = Note(pitch=64)
F = Note(pitch=65)
G = Note(pitch=67)
A = Note(pitch=69)


def build_synthesizer(attack=.1, decay=.2, sustain=.3, release=.4, wave_func=sine):
    """Create a monophonic synthesizer instance."""
    env = ADSR(attack, decay, sustain, release)
    osc = Oscillator(wave_func=wave_func)
    voice = Voice(osc, env)
    return MonophonicSynthesizer(voice)


# Arp synthesizer
arp = Arpeggiator(interval=5./16, order='alternating', initialNotes=[
    Alow, C, E, F, G, A,
])
synthesizer = build_synthesizer(wave_func=sawtooth)
lfo = Lfo(frequency=.1, wave_func=triangle, outputRange=(100, 3000))
fil = Filter(frequency=220.)
delay = Delay(time=0.76, feedback=.9)

# Bass synthesizer
sequencer = Sequencer(
    pattern=[[38, 41, 0, 0, 36, 34, 0, 0]],
    tempo=120,
    relNoteLength=1.,
    grid=WHOLE_NOTE,
)
bass = build_synthesizer(wave_func=sine, attack=4., sustain=1., release=4.)

# Make block connections
lfo | fil.frequency
mixer = (arp | synthesizer | fil | delay) + (sequencer | bass)
mixer.gains = [1., .3]
dac = mixer | Dac()

if __name__ == '__main__':
    run_klang(dac)
