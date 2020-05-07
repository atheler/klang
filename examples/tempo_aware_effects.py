from klang.audio.effects import Tremolo, Delay, Filter, Transformer
from klang.audio.klanggeber import KlangGeber
from klang.audio.mixer import StereoMixer
from klang.audio.oscillators import Oscillator, Lfo
from klang.audio.panning import LEFT, RIGHT
from klang.audio.waves import square, triangle, random
from klang.constants import STEREO
from klang.music.note_values import (
    LARGE_NOTE, WHOLE_NOTE, QUARTER_NOTE, DOTTED_QUARTER_NOTE,
    DOUBLE_DOTTED_QUARTER_NOTE
)


# Params
FEEDBACK = .8
DRY_WET = .4
FILEPATH = 'waterfall.wav'
FILEPATH = None


osc = Oscillator(wave_func=random)
tremolo = Tremolo(rate=QUARTER_NOTE, intensity=1., wave_func=square)
lfo = Lfo(LARGE_NOTE, wave_func=triangle)
trafo = Transformer.from_limits(lower=110., upper=1100)
fil = Filter()

# Stereo Delay
leftDelay = Delay(time=DOUBLE_DOTTED_QUARTER_NOTE, feedback=FEEDBACK, drywet=DRY_WET)
rightDelay = Delay(time=DOTTED_QUARTER_NOTE, feedback=FEEDBACK, drywet=DRY_WET)
mixer = StereoMixer(nInputs=STEREO, pannings=[LEFT, RIGHT])


with KlangGeber(nOutputs=STEREO, filepath=FILEPATH) as dac:
    osc.output.connect(tremolo.input)
    tremolo.output.connect(fil.input)
    lfo.output.connect(trafo.input)
    trafo.output.connect(fil.frequency)
    fil.output.connect(leftDelay.input)
    fil.output.connect(rightDelay.input)
    leftDelay.output.connect(mixer.inputs[0])
    rightDelay.output.connect(mixer.inputs[1])
    mixer.output.connect(dac.input)
