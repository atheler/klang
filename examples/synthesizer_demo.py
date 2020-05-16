"""Klang synthesizer demo."""
from klang.audio.envelopes import ADSR
from klang.audio.oscillators import Oscillator
from klang.audio.synthesizer import MonophonicSynthesizer, PolyphonicSynthesizer
from klang.audio.voices import OscillatorVoice
from klang.keyboard import MusicalKeyboard
from klang.klang import run_klang, Dac


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
dac = Dac(nChannels=1)


if __name__ == '__main__':
    keyboard.output.connect(synthesizer.input)
    synthesizer.output.connect(dac.input)
    run_klang(dac)
