"""Klang synthesizer demo."""
from klang.audio.envelope import ADSR
from klang.audio.oscillators import Oscillator
from klang.audio.synthesizer import MonophonicSynthesizer, PolyphonicSynthesizer
from klang.audio.voices import OscillatorVoice
from klang.keyboard import MusicalKeyboard
from klang.klang import Klang


# Params
MONOPHONIC = True


keyboard = MusicalKeyboard()
keyboard.start()  # Start keyboard daemon thread

#synthesizer = Synthesizer()
env = ADSR(.1, .2, .3, .4)
osc = Oscillator()
voice = OscillatorVoice(env, osc)

cls = MonophonicSynthesizer if MONOPHONIC else PolyphonicSynthesizer
synthesizer = cls(voice)#, policy='new')


if __name__ == '__main__':
    klang = Klang(nOutputs=1)
    keyboard.output.connect(synthesizer.input)
    synthesizer.output.connect(klang.dac.input)
    klang.start()
