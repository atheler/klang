"""Study on micro rhythms and swing.

"""
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.getcwd())
from klang.constants import TAU
from klang.music.metre import FOUR_FOUR_METRE
from klang.math import integrate
from klang.music.rhythm import swing
from klang.plotting import set_radian_xticks
from klang.plotting import nice_plotting_shape


def skewed_sine(x, skew=0.):
    """Skewed sine function."""
    assert -1 <= skew <= 1
    return np.sin(x + skew * np.sin(x))


def foo(phi, phase, nBeats):
    tmp = np.linspace(0, TAU, nBeats, False).reshape((nBeats, 1))
    idx = np.abs(phase - tmp).argmin(axis=1)
    return phi[idx]


if __name__ == '__main__':
    # Params
    polar = False
    N = 256
    metre = FOUR_FOUR_METRE

    phi, dPhi = np.linspace(0, TAU, N, endpoint=False, retstep=True)
    ratios = [
        .5,
        1.,
        2.,
    ]

    if polar:
        subplot_kw = dict(projection='polar')
    else:
        subplot_kw = {}

    shape = nice_plotting_shape(len(ratios))
    fig, axarr = plt.subplots(
        *shape, subplot_kw=subplot_kw,
        #sharex=True, sharey=True,
    )

    for ratio, ax in zip(ratios, np.ravel(axarr)):
        func = swing(ratio)
        phase = func(phi)
        omega = np.diff(phase, append=TAU) / dPhi

        ax.plot(phi, omega, label='Tempo $\omega(t)$')
        ax.plot(phi, phase, label='Bar Phase $\phi(t)$')

        cm = plt.get_cmap()
        for i, x in enumerate(foo(phi, phase, 8)):
            ax.axvline(x, ls=':', c=cm(x/TAU))

        set_radian_xticks(ax)
        title = 'Swing Ratio %.1f' % ratio
        ax.set_title(title)
        ax.grid(False)
        if polar:
            ax.set_rticks([])

    ax.legend()
    fig.suptitle('%s Swing' % metre)
    plt.show()
