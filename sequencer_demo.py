"""Sequencer drum kit demo."""
from klang.audio.effects import Delay
from klang.audio.klanggeber import KlangGeber
from klang.audio.mixer import Mixer
from klang.audio.sequencer import Sequencer, random_pattern
from klang.audio.synthesizer import Kick, HiHat, PolyphonicSynthesizer, MonophonicSynthesizer


from klang.audio.oscillators import Oscillator
from klang.audio.envelope import AR
from klang.audio.voices import OscillatorVoice


# Params
TEMPO = 120
PATTERN = [
    [ 60, 0, 0, 60, 0, 0, 60, 0, 60, 0, 0, 60, 0, 60, 0, 60, ],  # Kick drum
    4 * [0, 0, 127, 0],  # Hi-Hat
    #random_pattern(16, 5),
    [65, 70, 65, 68, 72, 65, 70, 65, 68, 72, 65, 70, 65, 68, 72, 65],  # Synthesizer
]
#FILEPATH = 'klang_output.wav'
FILEPATH = None

seq = Sequencer(
    PATTERN,
    tempo=TEMPO,
    #noteDuration=.8
    relNoteDuration=.8
)

kick = Kick(decay=.8)
hihat = HiHat()

# Create synthesizer
osc = Oscillator()
env = AR(.1, .02)
voice = OscillatorVoice(env, osc)
synthesizer = PolyphonicSynthesizer(voice)

mixer = Mixer(nInputs=3, gains=[.7, .1, 1.])
fx = Delay(delay=.25, feedback=.25)


with KlangGeber(nOutputs=1, filepath=FILEPATH) as dac:
    seq.output.connect(kick.input)
    seq.outputs[1].connect(hihat.input)
    seq.outputs[2].connect(synthesizer.input)
    kick.output.connect(mixer.inputs[0])
    hihat.output.connect(mixer.inputs[1])
    synthesizer.output.connect(fx.input)
    fx.output.connect(mixer.inputs[2])
    mixer.output.connect(dac.input)
