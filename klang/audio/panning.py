"""Audio left / right panning.

Resources:
  - http://www.cs.cmu.edu/~music/icm-online/readings/panlaws/
"""
import math
import functools

import numpy as np

from klang.constants import TAU


__all__ = ['LEFT', 'CENTER', 'RIGHT', 'panning_amplitudes', 'pan_signal']


LEFT = -1.
"""float: Maximum left panning value."""

CENTER = 0.
"""float: Center panning."""

RIGHT = 1.
"""float: Maximum right panning value."""


def pan_law_exponent(panLaw, centerAmplitude):
    """Calculate squish exponent values for pan law."""
    assert panLaw <= 0
    #return (panLaw - 10. * math.log10(2.)) / (2. * 10. * math.log10(centerAmplitude))
    return (panLaw - 20. * math.log10(2.)) / (2. * 20. * math.log10(centerAmplitude))


@functools.lru_cache()
def panning_amplitudes(panLevel, mode='constant_power', panLaw=None):
    """Calculate left / right panning amplitudes depending on calculation method
    and pan law.

    Args:
        panLevel (float): Panning level.

    Kwargs:
        mode (str): Panning mode. 'linear', 'constant_power' or 'mixture'.
        panLaw (float): Pan law in (negative) decibel.

    Returns:
        array: Left / right panning amplitudes.
    """
    if not mode in {'linear', 'constant_power', 'mixture'}:
        raise ValueError('Invalid panning mode %r!' % mode)
    if panLaw is not None and panLaw > 0:
        raise ValueError('Pan law has to be negative!')

    panLevel = np.clip(panLevel, LEFT, RIGHT)
    panAngle = TAU / 8 * (1. + panLevel)

    if mode == 'linear':
        left = .5 * (1. - panLevel)
        right = .5 * (1. + panLevel)
    elif mode == 'constant_power':
        left = np.cos(panAngle)
        right = np.sin(panAngle)
    elif mode == 'mixture':
        left = np.sqrt(.5 * (1. - panLevel) * np.cos(panAngle))
        right = np.sqrt(.5 * (1. + panLevel) * np.sin(panAngle))

    if panLaw is None:
        alpha = 1
    else:
        if mode == 'linear':
            alpha = pan_law_exponent(panLaw, .5)
        elif mode == 'constant_power':
            alpha = pan_law_exponent(panLaw, math.cos(TAU / 8))
        elif mode == 'mixture':
            centerValue = np.sqrt(.5 * np.cos(TAU / 8))
            alpha = pan_law_exponent(panLaw, centerValue)

    return np.array([
        [left ** alpha],
        [right ** alpha],
    ])


def pan_signal(signal, panLevel, mode='constant_power', panLaw=None):
    """Pan signal left to right stereo.

    Args:
        signal (array): Signal to pan. Either MONO or multiple channels.
        panLevel (float): Panning level.

    Kwargs:
        mode (str): Panning mode. 'linear', 'constant_power' or 'mixture'.
        panLaw (float): Pan law in (negative) decibel.

    Returns:
        array:
    """
    amplitudes = panning_amplitudes(panLevel, mode, panLaw)
    return amplitudes * signal


def demo():
    """Demo of different panning modes and pan laws. Also mono / stereo example."""
    import matplotlib.pyplot as plt

    # Params
    fs = 44100
    duration = 2.
    frequency = 7.89

    panning = np.linspace(-1., 1., 101)
    modes = ['linear', 'constant_power', 'mixture']
    panLaws = [None, 0, -3, -6]

    if True:
        fig, axarr = plt.subplots(len(modes), len(panLaws), sharex=True, sharey=True)

        if not hasattr(axarr, '__len__'):
            axarr = np.array([axarr])

        for mode, row in zip(modes, axarr):
            for panLaw, ax in zip(panLaws, row):
                left, right = panning_amplitudes(panning, mode=mode, panLaw=panLaw)
                #ax.plot(panning, left)
                #ax.plot(panning, right)
                power = left**2 + right**2
                ax.plot(panning, 10. * np.log(power))
                label = '%s, %s dB' % (mode, panLaw)
                ax.set_title(label)


        plt.show()


    if True:
        length = int(duration * fs)
        t = np.arange(length) / fs
        monoWave = np.sin(TAU * frequency * t)
        stereoWave = np.array([ monoWave, monoWave, ])
        panLevels = np.linspace(-1, 1, length)

        fig, axarr = plt.subplots(2, sharex=True, sharey=True)
        axarr[0].plot(t, pan_signal(monoWave, panLevels).T)
        axarr[0].set_title('Mono Signal')
        axarr[1].plot(t, pan_signal(stereoWave, panLevels).T)
        axarr[1].set_title('Stereo Signal')

        fig.suptitle('Pan from Left to Right')
        plt.xlabel('Time $t$')
        plt.ylim(-1, 1)
        for ax in fig.axes:
            ax.set_ylabel('Amplitude')

        plt.show()


if __name__ == '__main__':
    demo()
