import numpy as np

from config import SAMPLING_RATE, BUFFER_SIZE
from klang.blocks import Block
from klang.util import load_wave


DT = 1. / SAMPLING_RATE
"""float: Sampling interval."""

SILENCE = np.zeros(BUFFER_SIZE)
"""array: A piece of silence."""


class AudioFile(Block):

    """Audio file block.

    Single sample playback with varying playback speed.
    """

    def __init__(self, filepath, loop=True):
        self.rate, self.data = load_wave(filepath)
        super().__init__(nOutputs=self.n_channels)
        self.filepath = filepath
        self.loop = loop

        self.playing = True
        self.playingPosition = 0.
        self.playbackSpeed = 1.
        self.xp = np.arange(self.length) / self.rate

        self.mute_outputs()

    @property
    def length(self):
        """Number of samples."""
        return self.data.shape[0]

    @property
    def n_channels(self):
        """Number of audio channels."""
        return self.data.shape[1]

    @property
    def duration(self):
        """Duration of audio file in seconds."""
        return self.length / float(self.rate)

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
        for channel in self.outputs:
            channel.set_value(SILENCE)

    def update(self):
        if not self.playing:
            return self.mute_outputs()

        omega = self.playbackSpeed * np.arange(BUFFER_SIZE + 1)
        t = self.playingPosition + DT * omega
        if t[-1] >= self.duration and self.loop:
            self.pause()
            return self.mute_outputs()

        t %= self.duration
        self.playingPosition = t[-1]
        for chunk, channel in zip(self.data.T, self.outputs):
            samples = np.interp(t[:-1], self.xp, chunk)
            channel.set_value(samples)

    def __str__(self):
        state = 'Playing' if self.playing else 'Paused'
        return '%s(%s, %.3f / %.3f sec)' % (
            self.__class__.__name__,
            state,
            self.playingPosition,
            self.duration,
        )