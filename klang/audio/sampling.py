"""Audio sampling.

Note, for raw audio samples we use a different data layout then for our normal
audio samples. With multi channel audio axis=0 -> Time, axis=1 -> Channels.

TODO:
  - class Sampler
  - class Looper

Open Questions:
  - data vs. samples. Array orientation
"""
import numpy as np
import samplerate

from config import SAMPLING_RATE, BUFFER_SIZE
from klang.block import Block
from klang.connections import MessageInput
from klang.constants import MONO, ONE_D
from klang.util import load_wave


def is_audio_samples_shape(array):
    """Check if proper shape of audio samples."""
    array = np.asarray(array)
    if array.ndim == 0:
        return False

    if array.ndim == MONO:
        return True

    length, nChannels = array.shape
    return length > nChannels


def interp_2d(x, xp, fp, *args, **kwargs):
    """Multi-dimensional linear interpolation. Using np.interp."""
    fp = np.asarray(fp)
    if fp.ndim == ONE_D:
        return np.interp(x, xp, fp, *args, **kwargs)

    return np.array([
        np.interp(x, xp, col, *args, **kwargs) for col in fp.T
    ]).T


def extend_with_silence(array):
    """Append zeros to audio array for full buffer size. Not for raw audio
    samples. Shape ~ (STEREO, BUFFER_SIZE).
    """
    # TODO(atheler): What to do if length > BUFFER_SIZE? For now let's keep the
    # error raising.
    shape = array.shape
    length = shape[-1]
    if length == BUFFER_SIZE:
        return array

    ret = np.zeros(shape[:-1] + (BUFFER_SIZE,))
    ret[..., :length] = array
    return ret


def sum_to_mono(samples):
    """Sum samples to mono."""
    samples = np.asarray(samples)
    if samples.ndim != MONO:
        samples = np.mean(samples, axis=1)

    return samples.reshape((-1, 1))


class SampleProvider:

    """Sample callback. Provides new samples for samplerate interpolators via
    __call__. Supports audio trimming and looping.
    """

    def __init__(self, data, loop=False, start=0, stop=None):
        """Args:
            data (array): Data.

        Kwargs:
            loop (bool): Looped playback.
            start (int): Playback start.
            stop (int): Playback stop.
        """
        assert is_audio_samples_shape(data)
        self.data = data
        self.loop = loop
        self.start = 0
        self.stop = self.length

        self.currentIndex = 0
        self.trim(start, stop)

    @property
    def length(self):
        """Length of samples buffer."""
        return self.data.shape[0]

    @property
    def nChannels(self):
        """Length of samples buffer."""
        if self.data.ndim == MONO:
            return MONO

        return self.data.shape[1]

    @property
    def playing(self):
        """Still playing."""
        return self.currentIndex < self.stop

    def rewind(self):
        """Rewind to the beginning."""
        self.currentIndex = self.start

    def trim(self, start=0, stop=None):
        """Trim playback boundaries to [start, stop)."""
        stop = stop or self.length
        start = int(start)
        stop = int(stop)
        assert 0 <= start < stop <= self.length
        self.start = start
        self.stop = stop
        self.currentIndex = max(self.currentIndex, start)

    def __call__(self, nFrames=BUFFER_SIZE):
        """Get the next nFrames samples."""
        start = self.currentIndex
        stop = start + nFrames
        reachedEnd = (stop >= self.stop)
        if reachedEnd:
            if self.loop:
                stop = (stop % self.stop) + self.start
            else:
                # Block for future uses
                stop = self.stop

        self.currentIndex = stop
        if start <= stop:
            return self.data[start:stop]

        return np.concatenate([
            self.data[self.start:stop],
            self.data[start:self.stop],
        ])


class CrudeResampler:

    """Lo-fi resampler.

    Resampling via linear sample interpolation. No filtering occures so this
    adds lo-fi noise and jitter. The 'very_crude' mode additionally floors
    interpolation indices and and in this way adds even more distortion.

    Should work as a replacement of samplerate.CallbackResampler (no guarantee).
    """

    VALID_CONVERTER_TYPES = {'crude', 'very_crude'}
    """set: Valid modes."""

    def __init__(self, callback, ratio, converter_type='crude', channels=1):
        assert converter_type in self.VALID_CONVERTER_TYPES
        self.callback = callback
        self.ratio = ratio
        self.converter_type = converter_type
        self.channels = channels

    def set_starting_ratio(self, ratio):
        """Set sample rate conversion ratio for next read() call. Compatibility
        to samplerate.CallbackResampler API.
        """
        self.ratio = ratio

    def reset(self):
        """No effect. Compatibility to samplerate.CallbackResampler API."""
        pass

    def read(self, nFrames):
        # Fetch samples
        nSamplesNeeded = int(nFrames / self.ratio)
        fp = self.callback(nFrames=nSamplesNeeded)
        length = fp.shape[0]

        if length == 0:
            return np.zeros((0, self.channels))

        # Shrink nFrames if we did not get enough samples from SampleProvider.
        nFrames = (nFrames * length) // nSamplesNeeded

        # Linear sample interpolation
        x = np.linspace(0, length, nFrames, endpoint=False)
        if self.converter_type == 'very_crude':
            x = x.astype(int)

        xp = np.arange(length)
        return interp_2d(x, xp, fp)


class Resampler:

    """Audio sample container.

    Resample audio samples with different sampling rates and with varying playback speed.
    """

    VALID_SAMPLERATE_MODES = set(samplerate.converters.ConverterType.__members__)
    """set: Valid modes / samplerate converters."""

    VALID_MODES = VALID_SAMPLERATE_MODES.union(CrudeResampler.VALID_CONVERTER_TYPES)
    """set: All valid modes."""

    def __init__(self, rate, data, mode='linear', playbackSpeed=1., loop=False):
        assert mode in self.VALID_MODES
        self.rate = rate
        self.provider = SampleProvider(data, loop=loop)
        if mode in self.VALID_SAMPLERATE_MODES:
            cls = samplerate.CallbackResampler
        else:
            cls = CrudeResampler

        ratio = self.calculate_ratio(playbackSpeed)
        self.resampler = cls(
            self.provider,
            ratio=ratio,
            converter_type=mode,
            channels=self.provider.nChannels,
        )

    @property
    def length(self):
        return self.provider.length

    @property
    def nChannels(self):
        return self.provider.nChannels

    @property
    def currentIndex(self):
        return self.provider.currentIndex

    @property
    def playing(self):
        return self.provider.playing

    def calculate_ratio(self, playbackSpeed):
        return SAMPLING_RATE / self.rate / playbackSpeed

    def set_playback_speed(self, playbackSpeed):
        ratio = self.calculate_ratio(playbackSpeed)
        self.resampler.set_starting_ratio(ratio)

    def rewind(self):
        self.provider.rewind()
        self.resampler.reset()

    def read(self, nFrames=BUFFER_SIZE):
        return self.resampler.read(nFrames)

    def __str__(self):
        return '%s(%d / %d, %s)' % (
            self.__class__.__name__,
            self.provider.currentIndex,
            self.provider.length,
            'playing' if self.provider.playing else 'stopped'
        )


class AudioFile(Block):

    """Audio file block.

    Single sample playback with varying playback speed.
    """

    def __init__(self, data, rate=SAMPLING_RATE, mono=False, *args, **kwargs):
        assert is_audio_samples_shape(data)
        super().__init__(nOutputs=1)
        data = np.asarray(data)
        if mono and data.shape[1] > 1:
            data = sum_to_mono(data)

        self.resampler = Resampler(rate, data, *args, **kwargs)
        self.filepath = ''
        self.playing = False
        self.silence = np.zeros((self.resampler.nChannels, BUFFER_SIZE))
        self.mute_outputs()

    @classmethod
    def from_wave(cls, filepath, *args, **kwargs):
        """Load audio file from WAV file."""
        rate, data = load_wave(filepath)
        self = cls(data, rate, *args, **kwargs)
        self.filepath = filepath
        return self

    @property
    def playingPosition(self):
        return self.resampler.currentIndex / self.resampler.rate

    @property
    def duration(self):
        """Audio file total duration."""
        return self.resampler.length / self.resampler.rate

    def play(self):
        """Start playback."""
        self.playing = True

    def pause(self):
        """Pause playback."""
        self.playing = False

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
        if not self.playing:
            return self.mute_outputs()

        data = self.resampler.read(BUFFER_SIZE)
        self.playing = self.resampler.playing
        samples = extend_with_silence(data.T)
        self.output.set_value(samples)

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

    def __init__(self, data, rate=SAMPLING_RATE):
        super().__init__(nOutputs=1)
        self.inputs = [MessageInput(self)]

    @classmethod
    def from_wave(self, filepath):
        pass
