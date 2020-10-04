"""Arpeggiator demo revised / Aeolian Arp."""
from klang.arpeggiator import Arpeggiator
from klang.audio import (
    AR, Dac, Filter, Gain, HiHat, Kick, Lfo, MonophonicSynthesizer, Oscillator,
    PolyphonicSynthesizer, Reverb, StereoDelay, StereoMixer, Tremolo, Voice,
    sine, square, triangle,
)
from klang.klang import run_klang
from klang.music import (
    DOTTED_EIGHT_NOTE, DOUBLE_DOTTED_EIGHT_NOTE, EIGHT_NOTE, LONG_NOTE,
    QUARTER_NOTE,
)
from klang.sequencer import Sequencer


CHORDS = [
    (60, 63, 67, 70, 72),
    (62, 65, 67, 70, 72),
    (63, 65, 70, 72, 74),
    (55, 67, 70, 72, 74),
]


def build_synthesizer(cls=MonophonicSynthesizer, attack=.05, release=.4, wave_func=sine):
    """Create a synthesizer instance."""
    env = AR(attack, release)
    osc = Oscillator(wave_func=wave_func)
    voice = Voice(osc, env)
    return cls(voice)


mixer = StereoMixer()

# Kick drum
mixer += (
    Sequencer([
        60, 0, 0, 0, 0, 0, 0, 0,
        60, 0, 0, 0, 0, 0, 60, 0,
        60, 0, 0, 0, 0, 0, 0, 0,
        60, 0, 0, 0, 0, 0, 0, 60,
    ]) | Kick(frequency=33., decay=1.2, pitchDecay=.8)
)

# HiHat
mixer += (
    Sequencer([
        0, 0, 60, 0, 60, 0, 0, 0,
        0, 0, 0, 60, 0, 60, 0, 0,
        0, 0, 0, 0, 60, 0, 60, 0,
    ])
    | HiHat()
    | Reverb(decay=5., preDelay=.5)
    | StereoDelay(
        leftTime=DOTTED_EIGHT_NOTE,
        rightTime=DOUBLE_DOTTED_EIGHT_NOTE,
        leftFeedback=.9,
        rightFeedback=.9,
        drywet=.5)
    | Tremolo(EIGHT_NOTE, smoothness=.01, depth=1., dutyCycle=.5)
)

# Arp synthesizer
lfo = Lfo(.1, outputRange=(450, 2500))
fil = Filter()
lfo | fil.frequency
mixer += (
    # relNoteLength = 1. can lead to overlapping notes which will than
    # cancel out the arpeggio
    Sequencer(pattern=[CHORDS], grid=LONG_NOTE, relNoteLength=.99)
    | Arpeggiator(interval=EIGHT_NOTE*2/3, order='random')
    | build_synthesizer(PolyphonicSynthesizer, .05, .4, triangle)
    | fil
    | Gain(gain=PolyphonicSynthesizer.MAX_VOICES)
    | StereoDelay(
        leftTime=EIGHT_NOTE,
        rightTime=QUARTER_NOTE,
        leftFeedback=.7,
        rightFeedback=.8,
        drywet=.5)
)

# Bass
mixer += (
    Sequencer([
        36, 0, 36, 0, 0, 0, 0, 0,
        32, 0, 32, 0, 0, 0, 0, 0,
        34, 0, 34, 0, 0, 0, 0, 0,
    ], grid=EIGHT_NOTE)
    | build_synthesizer(MonophonicSynthesizer, .01, 2., square)
    | Filter(frequency=400)
)
mixer.gains = [2, .2, 1., 1.]
dac = mixer | Dac(2)

if __name__ == '__main__':
    run_klang(dac)
