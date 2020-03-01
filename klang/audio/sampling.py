"""Audio sampling.

TODO:
  - Better sample interpolation (no more jitter).
  - Audio trimming
  - class Sampler
  - class Looper
"""
import math

import numpy as np

from config import SAMPLING_RATE, BUFFER_SIZE
from klang.blocks import Block
from klang.connections import MessageInput
from klang.constants import MONO, TWO_D
from klang.util import load_wave


DT = 1. / SAMPLING_RATE
"""float: Sampling interval."""


INDICES = np.arange(BUFFER_SIZE)
"""array: Buffer base indices."""


def sum_to_mono(samples):
    """Sum samples to mono."""
    samples = np.asarray(samples)
    if samples.ndim != MONO:
        samples = np.mean(samples, axis=1)

    return samples.reshape((-1, 1))


def interp_2d(x, xp, fp, *args, **kwargs):
    """Multi-dimensional linear interpolation."""
    return np.array([
        np.interp(x, xp, col, *args, **kwargs) for col in fp.T
    ]).T


class SampleInterpolator:
    """Linear sample interpolation.

    Because of practically / performance we do not periodically interpolate but
    instead allow for an overflow segment which will be added at the end. That
    is `overflow` many samples will be continued at the end (no circular array
    issue). This overflow should be at least maxPlaybackSpeed * BUFFER_SIZE.
    This way we can assume that the sample time points are always ascending and
    to not wrap around % duration (we do not have to interpolate over all data
    points, only a sub-section).

    TODO:
      - Improove. Kill float jitter!
    """

    def __init__(self, rate, samples, overflow=BUFFER_SIZE):
        samples = np.asarray(samples)
        assert samples.ndim == TWO_D
        self.rate = rate
        self.length, self.nChannels = samples.shape
        self.duration = self.length / self.rate
        self.xp = np.arange(self.length + overflow) / rate
        self.fp = np.concatenate([samples, samples[:overflow]])

    def get_interval(self, x):
        """Get sub section interval."""
        start = int(x[0] * self.rate)
        stop = max(start + 1, int(math.ceil(x[-1] * self.rate)))
        return start, stop

    def __call__(self, x):
        x = np.atleast_1d(x)
        start, stop = self.get_interval(x)
        return interp_2d(x, self.xp[start:stop], self.fp[start:stop])


class AudioFile(Block):

    """Audio file block.

    Single sample playback with varying playback speed.
    """

    MAX_PLAYBACK_SPEED = 10.

    def __init__(self, samples, rate, loop=True, mono=False):
        super().__init__(nOutputs=1)
        if mono and samples.shape[1] > 1:
            samples = sum_to_mono(samples)

        overflow = int(self.MAX_PLAYBACK_SPEED * BUFFER_SIZE)
        self.samples = SampleInterpolator(rate, samples, overflow)
        self.loop = loop
        self.filepath = ''

        self.playing = False
        self.playingPosition = 0.
        self.playbackSpeed = 1.
        self.silence = np.zeros((self.samples.nChannels, BUFFER_SIZE))

        self.mute_outputs()

    @classmethod
    def from_wave(cls, filepath, loop=True):
        rate, data = load_wave(filepath)
        self = cls(data, rate, loop)
        self.filepath = filepath
        return self

    def play(self):
        """Start playback."""
        self.playing = True

    def pause(self):
        """Pause playback."""
        self.playing = False

    def rewind(self):
        """Rewind to beginning."""
        self.playingPosition = 0.

    def stop(self):
        """Stop playback."""
        self.pause()
        self.rewind()

    def mute_outputs(self):
        """Set outputs to zero signal."""
        self.output.set_value(self.silence)

    def get_stop(self):
        return self.playingPosition + self.playbackSpeed * DT * BUFFER_SIZE

    def update(self):
        if not self.playing:
            return self.mute_outputs()

        stop = self.get_stop()
        atEnd = stop >= self.samples.duration
        if atEnd and self.loop:
            self.pause()
            return self.mute_outputs()

        t = self.playingPosition + DT * self.playbackSpeed * INDICES
        self.playingPosition = stop % self.samples.duration

        chunk = self.samples(t)
        self.output.set_value(chunk.T)

    def __str__(self):
        if self.filepath:
            infos = [repr(self.filepath)]
        else:
            infos = []

        infos.extend([
            'Playing' if self.playing else 'Paused',
            '%.3f / %.3f sec' % (self.playingPosition, self.samples.duration),
        ])
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join(infos)
        )


class Sampler(Block):

    """Audio samlper.

    TODO: Make me!
    """

    def __init__(self, data):
        super().__init__(nOutputs=1)
        self.inputs = [MessageInput(self)]

    @classmethod
    def from_wave(self, filepath):
        pass
