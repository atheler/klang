"""Sequencer drum kit demo."""
from klang.audio.effects import Delay
from klang.audio.envelope import AR
from klang.audio.mixer import Mixer
from klang.audio.oscillators import Oscillator
from klang.audio.sequencer import Sequencer
from klang.audio.synthesizer import Kick, HiHat, PolyphonicSynthesizer, MonophonicSynthesizer
from klang.audio.voices import OscillatorVoice
from klang.klang import Klang


# Params
TEMPO = 120
PATTERN = [
    [60, 0, 0, 60, 0, 0, 60, 0, 60, 0, 0, 60, 0, 60, 0, 60],  # Kick drum
    4 * [0, 0, 127, 0],  # Hi-Hat
    #random_pattern(16, 5),
    [65, 70, 65, 68, 72, 65, 70, 65, 68, 72, 65, 70, 65, 68, 72, 65],  # Synthesizer
]
#FILEPATH = 'klang_output.wav'
FILEPATH = None

seq = Sequencer(
    PATTERN,
    tempo=TEMPO,
    relNoteDuration=.8
)

kick = Kick(decay=.8)
hihat = HiHat()

# Create synthesizer
osc = Oscillator()
env = AR(attack=.1, release=.02)
voice = OscillatorVoice(envelope=env, oscillator=osc)
synthesizer = PolyphonicSynthesizer(voice)

fx = Delay(time=.25, feedback=.25)
mixer = Mixer(nInputs=3, gains=[.7, .1, 1.])

klang = Klang(nOutputs=1, filepath=FILEPATH)
seq.output.connect(kick.input)
seq.outputs[1].connect(hihat.input)
seq.outputs[2].connect(synthesizer.input)
kick.output.connect(mixer.inputs[0])
hihat.output.connect(mixer.inputs[1])
synthesizer.output.connect(fx.input)
fx.output.connect(mixer.inputs[2])
mixer.output.connect(klang.dac.input)
klang.start()
