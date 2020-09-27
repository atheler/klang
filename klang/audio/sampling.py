"""Audio sampling.

Note, for raw audio samples we use a different data layout then for our normal
audio samples. With multi channel audio axis=0 -> Time, axis=1 -> Channels.

Two different array layouts for multi channel:
  - data: Raw audio samples obtained from WAV file. Shape ~ (length, nChannels).
    Time contiguous.
  - samples: Audio samples in the Klang network. Shape ~ (nChannels, length).
    Channels contiguous. Channel broadcastable (e.g. mono -> stereo like
    monoEnv * multiChannelSamples).

TODO:
  - class Sampler
  - class Looper
"""
import numpy as np
import samplerate

from klang.audio.envelopes import AR
from klang.audio.helpers import get_silence
from klang.audio.voices import Voice
from klang.audio.wavfile import load_wave
from klang.block import Block
from klang.config import SAMPLING_RATE, BUFFER_SIZE
from klang.connections import MessageInput
from klang.constants import MONO, ONE_D
from klang.math import clip
from klang.music.tunings import EQUAL_TEMPERAMENT


__all__ = [
    'AudioFile', 'CRUDE_RESAMPLER_MODES', 'CrudeResampler', 'Sample',
    'SampleVoice', 'Sampler', 'VALID_MODES', 'number_of_channels',
    'sum_to_mono',
]


SAMPLERATE_CONVERTER_TYPES = set(samplerate.converters.ConverterType.__members__)
"""set: All possible converter types of samplerate library."""

CRUDE_RESAMPLER_MODES = {'crude', 'very_crude'}
"""set: All possible modes for CrudeResampler."""

VALID_MODES = SAMPLERATE_CONVERTER_TYPES.union(CRUDE_RESAMPLER_MODES)
"""set: All possible resampler modes."""


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


def is_audio_samples_shape(array):
    """Check if proper shape of audio samples."""
    array = np.asarray(array)
    if array.ndim == 0:
        return False

    if array.ndim == MONO:
        return True

    length, nChannels = array.shape
    return length > nChannels


def number_of_channels(samples):
    """Number of audio channels."""
    if samples.ndim == MONO:
        return MONO

    return samples.shape[0]


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
        """Try to read the next nFrames. samplerate style. Can return less then
        the requested nFrames!.
        """
        # Fetch samples
        nSamplesNeeded = int(nFrames / self.ratio)
        data = self.callback(nFrames=nSamplesNeeded)
        length = data.shape[0]
        if length == 0:
            return np.zeros((0, self.channels))

        # Shrink nFrames if we did not get enough samples from SampleProvider.
        nFrames = (nFrames * length) // nSamplesNeeded

        # Linear sample interpolation
        x = np.linspace(0, length, nFrames, endpoint=False)
        if self.converter_type == 'very_crude':
            return data[x.astype(int)]

        xp = np.arange(length)
        return interp_2d(x, xp, data)


def initialize_resampler(callback, ratio, mode, channels):
    """Initialize a resampler instance. Either samplerate.CallbackResampler or
    CrudeResampler depending on mode.

    Args:
        callback (function): Sample callback.
        ratio (float): Convertion rate.
        mdoe (str): Converter type.
        channels (int): Number of audio channels.

    Returns:
        samplerate.CallbackResampler or CrudeResampler: Instance.
    """
    assert mode in VALID_MODES

    # Select resampler type
    if mode in SAMPLERATE_CONVERTER_TYPES:
        cls = samplerate.CallbackResampler
    else:
        cls = CrudeResampler

    resampler = cls(
        callback,
        ratio,
        converter_type=mode,
        channels=channels,
    )
    return resampler


class Sample:

    """Audio sample container.

    Resample audio samples with different sampling rates and with varying
    playback speed. Audio samples are passed to resampler via the callback()
    method. New samples can be acuired via calling the read() method.
    """

    def __init__(self, rate, data, start=0, stop=None, loop=False,
                 playbackSpeed=1., mode='linear'):
        """Args:
            rate (float): Sampling rate.
            data (array): Samples.

        Kwargs:
            start (int): Start sample index.
            stop (int): Stop sample index. End of audio samples by default.
            loop (bool): Loop samples.
            playbackSpeed (float): Playback speed. 1.0 is normal speed.
            mode (str): Resampling mode.
        """
        assert is_audio_samples_shape(data)
        self.rate = rate
        self.data = data
        self.start = 0
        self.stop = self.length
        self.loop = loop

        self.currentIndex = 0
        self.trim(start, stop)
        self.resampler = initialize_resampler(
            self.callback,
            self.calculate_ratio(playbackSpeed),
            mode,
            self.nChannels,
        )

    @property
    def length(self):
        """Length of samples buffer."""
        return self.data.shape[0]

    @property
    def nChannels(self):
        """Length of samples buffer."""
        return number_of_channels(self.data.T)

    @property
    def playing(self):
        """Still playing."""
        return self.currentIndex < self.stop

    def rewind(self):
        """Rewind to the beginning."""
        self.currentIndex = self.start
        self.resampler.reset()

    def trim(self, start=0, stop=None):
        """Trim playback boundaries to [start, stop)."""
        start = int(start)
        stop = int(stop or self.length)
        assert 0 <= start < stop <= self.length  # TODO(atheler): start <= stop?
        self.start = start
        self.stop = stop
        self.currentIndex = clip(self.currentIndex, start, stop)

    def calculate_ratio(self, playbackSpeed):
        """Calculate reample ratio from playback speed."""
        return SAMPLING_RATE / self.rate / playbackSpeed

    def set_playback_speed(self, playbackSpeed):
        """Set playback speed for next read() call."""
        ratio = self.calculate_ratio(playbackSpeed)
        self.resampler.set_starting_ratio(ratio)

    def callback(self, nFrames=BUFFER_SIZE):
        """Sample callback. Get some new samples for resampler."""
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

    def read(self, nFrames=BUFFER_SIZE):
        """Get next samples."""
        return self.resampler.read(nFrames)


class AudioFile(Block):

    """Audio file block.

    Single sample playback from WAV.
    """

    def __init__(self, filepath, mono=False, *args, **kwargs):
        """Args:
            filepath (str): WAV filepath.

        Kwargs:
            mono (bool): Sum samples to mono.

        *args, **kwargs: Arguments for Sample instance.
        """
        rate, data = load_wave(filepath)
        assert is_audio_samples_shape(data)
        super().__init__(nOutputs=1)
        if mono and data.shape[1] > 1:
            data = sum_to_mono(data)

        self.filepath = filepath

        self.sample = Sample(rate, data, *args, **kwargs)
        self.playing = False
        shape = (self.sample.nChannels, BUFFER_SIZE)
        self.silence = get_silence(shape)
        self.mute_outputs()

    @property
    def playingPosition(self):
        """Current playback position."""
        return self.sample.currentIndex / self.sample.rate

    @property
    def duration(self):
        """Audio files total duration."""
        return self.sample.length / self.sample.rate

    def play(self):
        """Start playback."""
        self.playing = True

    def pause(self):
        """Pause playback."""
        self.playing = False

    def rewind(self):
        """Rewind to beginning."""
        self.sample.rewind()

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

        data = self.sample.read(BUFFER_SIZE)
        self.playing = self.sample.playing
        samples = extend_with_silence(data.T)
        samples = (samples.T).squeeze()
        self.output.set_value(samples)

    def __str__(self):
        infos = []
        if self.filepath:
            infos = [repr(self.filepath)]

        infos.extend([
            'Playing' if self.playing else 'Paused',
            '%.3f / %.3f sec' % (self.playingPosition, self.duration),
        ])
        return '%s(%s)' % (type(self).__name__, ', '.join(infos))


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


_C_FREQUENCY = EQUAL_TEMPERAMENT.pitch_2_frequency(60)


class SampleVoice(Voice):

    """Basic sample voice."""

    def __init__(self, rate, data, baseFrequency=_C_FREQUENCY, envelope=None,
                 *args, **kwargs):
        super().__init__(envelope or AR(attack=0.00, release=.1))
        self.baseFrequency = baseFrequency
        self.sample = Sample(rate, data, *args, **kwargs)

    def process_note(self, note):
        super().process_note(note)
        if note.on:
            self.sample.rewind()
            freq = note.frequency / self.baseFrequency
            self.sample.set_playback_speed(freq)

    def update(self):
        super().update()
        samples = self.sample.read().T
        env = self.envelope.output.value
        signal = self.amplitude * env * extend_with_silence(samples)
        self.output.set_value(signal)
        #self.output.set_value(env * extend_with_silence(samples))
