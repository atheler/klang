"""Audio sampling.

TODO:
  - Audio trimming
  - class Sampler
  - class Looper
  - Some incorporate old, lo-fi linear sample interpolation.
"""
import numpy as np
import samplerate

from config import SAMPLING_RATE, BUFFER_SIZE
from klang.blocks import Block
from klang.connections import MessageInput
from klang.constants import MONO
from klang.util import load_wave


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


class Resampler:

    """Resample with varying playing speed."""

    def __init__(self, rate, data, converter_type='linear', playbackSpeed=1.,
                 loop=False):
        """Kwargs:
            converter_type (str): See samplerate. Possebilites are: 'linear',
                'sinc_best', 'sinc_fastest', 'sinc_medium' and
                'zero_order_hold'.
        """
        self.rate = rate
        self.data = np.asarray(data)
        self.playbackSpeed = playbackSpeed
        self.loop = loop

        self.resampler = samplerate.CallbackResampler(
            self.callback,
            ratio=SAMPLING_RATE / self.rate / self.playbackSpeed,
            converter_type=converter_type,
            channels=self.nChannels,
        )
        self.index = 0
        self.playing = True

    @property
    def length(self):
        return self.data.shape[0]

    @property
    def nChannels(self):
        if self.data.ndim == MONO:
            return MONO

        return self.data.shape[1]

    def callback(self):
        if not self.playing:
            return

        start = self.index
        stop = (start + BUFFER_SIZE) % self.length

        if start < stop:
            #print('Here', stop-start)
            self.index = stop
            return self.data[start:stop]

        if self.loop:
            self.index = stop
            return np.concatenate([
                self.data[start:],
                self.data[:stop],
            ])

        self.playing = False
        return self.data[start:]

    def rewind(self):
        self.index = 0
        self.resampler.reset()

    def read(self, nFrames):
        """Read next nFrames."""
        frames = self.resampler.read(nFrames)
        n = frames.shape[0]
        if n == nFrames:
            return frames

        if self.nChannels == MONO:
            ret = np.zeros(nFrames)
        else:
            ret = np.zeros((nFrames, self.nChannels))

        if n == 0:
            return ret

        ret[:n] = frames
        return ret

    def set_playback_speed(self, playbackSpeed):
        ratio = SAMPLING_RATE / self.rate / playbackSpeed
        self.resampler.set_starting_ratio(ratio)

    def __str__(self):
        return '%s(%d / %d, %s)' % (
            self.__class__.__name__,
            self.index,
            self.length,
            'playing' if self.playing else 'stopped'
        )


class AudioFile(Block):

    """Audio file block.

    Single sample playback with varying playback speed.
    """

    def __init__(self, data, rate=SAMPLING_RATE, mono=False, *args, **kwargs):
        super().__init__(nOutputs=1)
        data = np.asarray(data)
        if mono and data.shape[1] > 1:
            data = sum_to_mono(data)

        self.resampler = Resampler(rate, data, *args, **kwargs)
        self.filepath = ''
        self.silence = np.zeros((self.resampler.nChannels, BUFFER_SIZE))
        self.mute_outputs()

    @classmethod
    def from_wave(cls, filepath, *args, **kwargs):
        rate, data = load_wave(filepath)
        self = cls(data, rate, *args, **kwargs)
        self.filepath = filepath
        return self

    @property
    def playingPosition(self):
        return self.resampler.index / self.resampler.rate

    @property
    def duration(self):
        return self.resampler.length / self.resampler.rate

    def play(self):
        """Start playback."""
        self.resampler.playing = True

    def pause(self):
        """Pause playback."""
        self.resampler.playing = False

    def rewind(self):
        """Rewind to beginning."""
        self.resampler.rewind()

    def stop(self):
        """Stop playback."""
        self.pause()
        self.rewind()

    def mute_outputs(self):
        """Set outputs to zero signal."""
        self.output.set_value(self.silence)

    def update(self):
        if not self.resampler.playing:
            return self.mute_outputs()

        frames = self.resampler.read(BUFFER_SIZE)
        self.output.set_value(frames.T)

    def __str__(self):
        if self.filepath:
            infos = [repr(self.filepath)]
        else:
            infos = []

        infos.extend([
            'Playing' if self.resampler.playing else 'Paused',
            '%.3f / %.3f sec' % (self.playingPosition, self.duration),
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
