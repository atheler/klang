"""Klang synthesizer demo."""
from klang.audio.klanggeber import KlangGeber
from klang.audio.synthesizer import MonophonicSynthesizer, PolyphonicSynthesizer
from klang.keyboard import MusicalKeyboard
from klang.audio.voices import OscillatorVoice
from klang.audio.oscillators import Oscillator
from klang.audio.envelope import ADSR


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
    with KlangGeber(nOutputs=1) as dac:
        keyboard.output.connect(synthesizer.input)
        synthesizer.output.connect(dac.input)
