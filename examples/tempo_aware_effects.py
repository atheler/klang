"""Demonstration of tempo aware effects."""
from klang.audio import (
    Tremolo, Filter, StereoDelay, Oscillator, Lfo, square, triangle, random
)
from klang.constants import STEREO
from klang.klang import run_klang, Dac
from klang.music.note_values import (
    LARGE_NOTE, QUARTER_NOTE, DOTTED_QUARTER_NOTE, DOUBLE_DOTTED_QUARTER_NOTE
)


# Params
FEEDBACK = .8
DRY_WET = .4


if __name__ == '__main__':
    # Init blocks
    osc = Oscillator(wave_func=random)
    tremolo = Tremolo(rate=QUARTER_NOTE, intensity=1., wave_func=square)
    lfo = Lfo(LARGE_NOTE, wave_func=triangle, outputRange=(110, 1100))
    fil = Filter()
    delay = StereoDelay(
        leftTime=DOUBLE_DOTTED_QUARTER_NOTE,
        rightTime=DOTTED_QUARTER_NOTE,
        leftFeedback=FEEDBACK,
        rightFeedback=FEEDBACK,
        drywet=DRY_WET,
    )
    dac = Dac(nChannels=STEREO)

    # Connect blocks
    osc | tremolo | fil.input | delay | dac
    lfo | fil.frequency

    run_klang(dac)
