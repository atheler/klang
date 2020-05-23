"""Klang synthesizer demo."""
from klang.audio import ADSR, Dac, MonophonicSynthesizer, Oscillator, OscillatorVoice
from klang.keyboard import MusicalKeyboard
from klang.klang import run_klang, Dac


if __name__ == '__main__':
    keyboard = MusicalKeyboard()
    keyboard.start()  # Start keyboard daemon thread

    # Create synthesizer
    env = ADSR(.1, .2, .3, .4)
    osc = Oscillator()
    voice = OscillatorVoice(env, osc)
    synthesizer = MonophonicSynthesizer(voice)

    dac = Dac(nChannels=1)
    keyboard | synthesizer | dac

    run_klang(dac)
