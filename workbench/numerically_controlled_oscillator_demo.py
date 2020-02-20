#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Numerically-controlled oscillator demo.

Resources:
  - https://en.wikipedia.org/wiki/Numerically-controlled_oscillator

Author: atheler
"""
import math

import numpy as np
import matplotlib.pyplot as plt


TAU = 2. * math.pi
"""float: Circle constant."""

CLOCK_FREQUENCY = 100 * 1000 * 1000
"""int: Clock frequency in Hz."""

N = 32
"""int: Phase accumulator register bit width. Defines frequency resolution /
smallest possible frequency.
"""

M = 8
"""int: Phase to amplitude converter / lookup table size."""

DURATION = .01
"""float: Duration of demo plot in seconds."""

FREQUENCIES = [20, 440, 5555.555]
"""list: Demo plot frequencies."""


def frequency_resolution(clockFrequency, nBits):
    """Frequency resolution of numerically-controlled oscillator."""
    return clockFrequency / (2 ** nBits)


def find_fcw(frequency, clockFrequency, nBits):
    """Determine frequency controlling word. Delta phase increment per clock
    cycle for a given frequency.
    """
    freqRes = frequency_resolution(clockFrequency, nBits)
    return int(frequency // freqRes)


def sine_lookup_table(nBits):
    """Build sine lookup table for a given size.

    Usage:
        >>> print(sine_lookup_table(2))
        [ 0.0000000e+00  1.0000000e+00  1.2246468e-16 -1.0000000e+00]
    """
    length = int(2 ** nBits)
    phase = np.linspace(0, TAU, length, endpoint=False)
    return np.sin(phase)


def truncate(number, n, m):
    """Truncate number from n to m bits. Take first (n - m) bits as output.

    Usage:
        >>> number = 15
        ... print(bin(number))  # 4 bits
        0b1111

        >>> trunc = truncate(number, 4, 2)
        ... print(bin(trunc))  # 2 bits
        0b11
    """
    return number >> (n - m)


if __name__ == '__main__':
    print('Clock frequency: %d Hz' % CLOCK_FREQUENCY)
    print('Phase accumulator word width: %d bits' % N)
    print('Frequency resolution %.3f Hz' % frequency_resolution(CLOCK_FREQUENCY, N))

    lut = sine_lookup_table(M)

    print('Sine lookup table with %d entries' % len(lut))

    length = int(DURATION * CLOCK_FREQUENCY)
    clock = np.arange(length)
    fig, (ax0, ax1) = plt.subplots(2, 1, sharex=True)
    for freq in FREQUENCIES:
        fcw = find_fcw(freq, CLOCK_FREQUENCY, N)
        acc = (clock * fcw) % (2 ** N)

        label = '%.1f Hz' % freq
        ax0.plot(clock, acc, label=label)

        idx = truncate(acc, N, M)
        signal = lut[idx]

        ax1.plot(clock, signal, label=label)

    # Annotate plot
    ax0.set_title('Phase Accumulator')
    ax1.set_title('Output Signal')
    ax1.set_xlabel('Clock Cycles')
    fig.suptitle('Clock %s Hz, PA bits %d, LUT bits %d' % (CLOCK_FREQUENCY, N, M))
    for ax in fig.axes:
        ax.legend()

    plt.show()
