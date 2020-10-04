"""Reverb demo."""
from klang.audio import AR, MonophonicSynthesizer, Oscillator, Reverb, Voice
from klang.klang import Dac, run_klang
from klang.music.note_values import DOTTED_EIGHT_NOTE, QUARTER_NOTE, SIXTEENTH_NOTE
from klang.sequencer import Sequencer


# Params
TEMPO = 120.


def create_synthesizer(attack=.01, release=1.):
    """Create a monophonic synthesizer instance."""
    osc = Oscillator()
    env = AR(attack, release)
    voice = Voice(osc, env)
    return MonophonicSynthesizer(voice)


# Init the 3x rhythmically interlaced synthesizer voices: base (1/4), upper
# (1/16) and lower (.1/8).
base = Sequencer([
    60, 62, 67, 69,
    60, 62, 67, 69,
    60, 62, 67, 71,
], TEMPO, grid=QUARTER_NOTE, relNoteLength=.125) | create_synthesizer()
upper = Sequencer([
    0, 0, 0, 0, 0, 0, 76, 0, 0, 72, 0, 0, 0, 0, 0, 0,
], TEMPO, grid=SIXTEENTH_NOTE, relNoteLength=.5) | create_synthesizer()
lower = Sequencer([
    53, 60, 55, 60, 57, 60, 62, 60,
], TEMPO, grid=DOTTED_EIGHT_NOTE, relNoteLength=.25) | create_synthesizer()
mixer = (base + upper + lower)
dac = mixer | Reverb(decay=3., dryWet=.7) | Dac()

if __name__ == '__main__':
    run_klang(dac)
