"""Klang synthesizer demo."""
from klang.audio import ADSR, Dac, MonophonicSynthesizer, Oscillator, Voice
from klang.keyboard import MusicalKeyboard
from klang.klang import run_klang


if __name__ == '__main__':
    keyboard = MusicalKeyboard()
    keyboard.start()  # Start keyboard daemon thread

    # Create synthesizer
    env = ADSR(.1, .2, .3, .4)
    osc = Oscillator()
    voice = Voice(osc, env)
    synthesizer = MonophonicSynthesizer(voice)

    run_klang(keyboard | synthesizer | Dac())
