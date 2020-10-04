#!/usr/bin/env python3
"""Psuedo harmonic series and looping envelope voices. Different variations
(VARIATION 0, 1 or 2).
"""
import fractions

from klang.audio import (
    AR, Dac, Oscillator, StereoMixer, Voice, sine, triangle
)
from klang.constants import STEREO
from klang.klang import run_klang
from klang.math import blend
from klang.messages import Note


# Params
VARIATION = 2
"""int: Variation number (0, 1, or 2)."""

N_VOICES = 20
"""int: Maximum number of voices."""

RATIO = .02
"""float: Ratio how duration will be split between attack / release time."""


def calc_velocity(voiceNr, minVel=.1):
    """Get decreasing velocity values for higher numbered voices."""
    alpha = voiceNr / (N_VOICES - 1)
    return blend(1., minVel, alpha)


def alternating_panning(voiceNr):
    """Get alternating pan levels. From the center to the outers. Like 0., -.1,
    .1, -.2, .2, -.3, 3, ...
    """
    panLevel = voiceNr / (N_VOICES - 1)
    if voiceNr % 2:
        return -1 * panLevel
    else:
        return panLevel


def get_voice_params(voiceNr):
    """Get the parameters for the different variations."""
    if VARIATION == 0:
        frac = voiceNr + 1
        duration = 5 / frac
        wave_func = triangle
        frequency = 55. * frac
        minVel = .0

    elif VARIATION == 1:
        frac = fractions.Fraction(voiceNr+2, voiceNr+1)
        duration = 1 / frac
        wave_func = triangle
        frequency = 440. / frac
        minVel = .5

    elif VARIATION == 2:
        frac = fractions.Fraction(voiceNr+2, voiceNr+1)
        duration = 5 + 5 / frac
        wave_func = sine
        frequency = 440. / frac
        minVel = .5

    else:
        raise ValueError('Invalid variation number %d' % VARIATION)

    velocity = calc_velocity(voiceNr, minVel)
    panLevel = alternating_panning(voiceNr)
    return duration, wave_func, frequency, velocity, panLevel


mixer = StereoMixer()
for voiceNr in range(N_VOICES):
    duration, wave_func, frequency, velocity, panLevel = get_voice_params(voiceNr)

    # Setup voice
    osc = Oscillator(wave_func=wave_func)  # frequency will be set by note
    attack = RATIO * duration
    release = (1 - RATIO) * duration
    env = AR(attack, release, loop=True)
    voice = Voice(osc, env)
    mixer += voice
    mixer.pannings[-1] = panLevel

    # Activate voice (dummy pitch number)
    note = Note(0, velocity, frequency=frequency)
    voice.input.push(note)

dac = mixer | Dac(nChannels=STEREO)

if __name__ == '__main__':
    run_klang(dac)
