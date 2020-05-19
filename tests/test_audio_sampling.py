import functools
import io
import unittest

import numpy as np
import scipy.io.wavfile

from klang.config import SAMPLING_RATE, BUFFER_SIZE
from klang.audio.helpers import MONO_SILENCE, STEREO_SILENCE
from klang.audio.sampling import (
    extend_with_silence, interp_2d, Sample, AudioFile, VALID_MODES,
    number_of_channels
)
from klang.constants import TAU, MONO, STEREO
from klang.audio.wavfile import convert_samples_to_int

MULTI_CHANNEL_SILENCE = np.zeros((5, BUFFER_SIZE))
LONG = int(10. * SAMPLING_RATE)
SHORT = 4 * BUFFER_SIZE
CASES = [
    {'length': SHORT, 'channels': MONO},
    {'length': SHORT, 'channels': STEREO},
    {'length': SHORT, 'channels': 5},
    {'length': LONG, 'channels': MONO},
    {'length': LONG, 'channels': STEREO},
    {'length': LONG, 'channels': 5},
]


@functools.lru_cache(maxsize=64)
def generate_audio_data(duration=1., channels=1, length=None, fs=SAMPLING_RATE):
    """Generate 440Hz sine audio data."""
    length = length or int(duration * fs)
    dt = 1. / fs
    t = dt * np.arange(length)
    monoSignal = np.sin(TAU * 440. * t)
    if channels == MONO:
        return monoSignal

    return np.array(channels * [monoSignal]).T


def pack_audio_data_in_file(data, fs=SAMPLING_RATE):
    """Pack audio data in WAV-file-like io object."""
    filelike = io.BytesIO()
    dataInt = convert_samples_to_int(data)
    scipy.io.wavfile.write(filelike, fs, dataInt)
    filelike.seek(0)
    return filelike


def all_zero(array):
    """Check if all array values are zero."""
    return np.count_nonzero(array) == 0


class TestInterp2d(unittest.TestCase):
    def test_1d(self):
        xp = np.array([0, 2])
        fp = np.array([0., 4.])
        np.testing.assert_equal(
            interp_2d([0, 1, 2], xp, fp),
            [0, 2, 4],
        )

    def test_2d(self):
        xp = np.array([0, 2])
        fp = np.array([[0., 0.], [2., 4.]])

        np.testing.assert_equal(
            interp_2d([0, 1, 2], xp, fp),
            [[0., 0.], [1., 2.], [2., 4.]]
        )

class TestExpandWithSilence(unittest.TestCase):
    def test_with_different_cases(self):
        np.testing.assert_equal(extend_with_silence(MONO_SILENCE), MONO_SILENCE)
        np.testing.assert_equal(extend_with_silence(STEREO_SILENCE), STEREO_SILENCE)
        np.testing.assert_equal(extend_with_silence(MULTI_CHANNEL_SILENCE), MULTI_CHANNEL_SILENCE)
        np.testing.assert_equal(extend_with_silence(np.zeros(100)), MONO_SILENCE)
        np.testing.assert_equal(extend_with_silence(np.zeros((2, 100))), STEREO_SILENCE)
        np.testing.assert_equal(extend_with_silence(np.zeros((5, 6))), MULTI_CHANNEL_SILENCE)


class TestSample(unittest.TestCase):
    def test_attributes(self):
        samples = np.arange(10)
        provider = Sample(SAMPLING_RATE, samples)

        self.assertEqual(provider.length, 10)
        self.assertEqual(provider.start, 0)
        self.assertEqual(provider.currentIndex, 0)
        self.assertEqual(provider.stop, 10)
        self.assertTrue(provider.playing)

    def test_non_looping(self):
        for kwargs in CASES:
            data = generate_audio_data(**kwargs)
            provider = Sample(SAMPLING_RATE, data, loop=False)
            while True:
                chunk = provider.callback()
                if chunk.shape[0] < BUFFER_SIZE:
                    assert 0 <= chunk.shape[0] < BUFFER_SIZE
                    break

            chunk = provider.callback()
            assert chunk.shape[0] == 0

    def test_looping(self):
        for kwargs in CASES:
            data = generate_audio_data(**kwargs)
            provider = Sample(SAMPLING_RATE, data, loop=True)
            for _ in range(len(data) // BUFFER_SIZE + 10):
                chunk = provider.callback()
                assert chunk.shape[0] == BUFFER_SIZE

    def test_wrong_clipping_arguments(self):
        toLong = len(MONO_SILENCE) + 1
        with self.assertRaises(AssertionError):
            Sample(SAMPLING_RATE, MONO_SILENCE, start=-5)

        with self.assertRaises(AssertionError):
            Sample(SAMPLING_RATE, MONO_SILENCE, stop=toLong)

        with self.assertRaises(AssertionError):
            Sample(SAMPLING_RATE, MONO_SILENCE, start=10, stop=5)

    def test_audio_sample_trimming(self):
        data = np.arange(15)
        provider = Sample(SAMPLING_RATE, data)

        provider.trim(start=2, stop=11)

        np.testing.assert_equal(provider.callback(nFrames=4), [2, 3, 4, 5])
        np.testing.assert_equal(provider.callback(nFrames=4), [6, 7, 8, 9])
        np.testing.assert_equal(provider.callback(nFrames=4), [10])
        np.testing.assert_equal(provider.callback(nFrames=4), [])


class TestResampler(unittest.TestCase):
    def test_mono_with_all_modes(self):
        bufferSize = 256
        data = generate_audio_data(duration=.1, channels=MONO)
        length = data.shape[0]
        for mode in VALID_MODES:
            resampler = Sample(SAMPLING_RATE, data, mode=mode)
            for _ in range(length // bufferSize):
                chunk = resampler.read()

                self.assertEqual(chunk.shape, (bufferSize, ))

            chunk = resampler.read()

            self.assertLess(chunk.shape[0], bufferSize)

    def test_stereo_with_all_modes(self):
        bufferSize = 256
        data = generate_audio_data(duration=.1, channels=STEREO)
        length = data.shape[0]
        for mode in VALID_MODES:
            resampler = Sample(SAMPLING_RATE, data, mode=mode)
            for _ in range(length // bufferSize):
                chunk = resampler.read()

                self.assertEqual(chunk.shape, (bufferSize, STEREO))

            chunk = resampler.read()

            self.assertLess(chunk.shape[0], bufferSize)

    def test_varying_playback_speed(self):
        data = generate_audio_data(duration=1., channels=MONO)
        for mode in VALID_MODES:
            playbackSpeed = .1
            resampler = Sample(SAMPLING_RATE, data, mode=mode, playbackSpeed=playbackSpeed)
            for _ in range(100):
                chunk = resampler.read()
                if len(chunk) < BUFFER_SIZE:
                    break

                playbackSpeed += .05
                resampler.set_playback_speed(playbackSpeed)

    def test_rewind(self):
        data = generate_audio_data(duration=1., channels=MONO)
        for mode in VALID_MODES:
            pass


class TestAudioFile(unittest.TestCase):
    def test_from_wave_file(self):
        for channels in [MONO, STEREO]:
            data = generate_audio_data(length=SAMPLING_RATE, channels=channels)
            filelike = pack_audio_data_in_file(data)
            af = AudioFile(filelike)

    def test_attributes(self):
        for channels in [MONO, STEREO]:
            data = generate_audio_data(length=SAMPLING_RATE, channels=channels)
            filelike = pack_audio_data_in_file(data)
            af = AudioFile(filelike)

            self.assertEqual(af.playingPosition, 0.)
            self.assertEqual(af.duration, 1.0)
            self.assertEqual(af.playing, False)

    def test_playback(self):
        for channels in [MONO, STEREO]:
            data = generate_audio_data(length=SAMPLING_RATE, channels=channels)
            filelike = pack_audio_data_in_file(data)
            af = AudioFile(filelike)

            af.update()

            assert all_zero(af.output.value)

            af.play()
            firstBatch = 100
            for _ in range(firstBatch):
                af.update()
                assert not all_zero(af.output.value)

            af.pause()
            af.update()

            assert all_zero(af.output.value)
            self.assertEqual(af.playingPosition, firstBatch * BUFFER_SIZE / SAMPLING_RATE)

            nChunks = len(data) // BUFFER_SIZE
            secondBatch = nChunks - firstBatch
            af.play()
            for _ in range(secondBatch):
                af.update()
                assert not all_zero(af.output.value)

            # Read remaining samples
            af.update()

            assert not all_zero(af.output.value)

            # Sample samples should be empty by now
            af.update()
            assert all_zero(af.output.value)


class TestNumberOfChannels(unittest.TestCase):
    def test_number_of_channels(self):
        monoSignal = np.zeros(10)

        self.assertEqual(number_of_channels(monoSignal), MONO)

        tenChannelSignal = np.zeros((10, 100))

        self.assertEqual(number_of_channels(tenChannelSignal), 10)


if __name__ == '__main__':
    unittest.main()
